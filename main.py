from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Query
from authlib.integrations.starlette_client import OAuth
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from dotenv import load_dotenv
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from fastapi_utils.tasks import repeat_every
from sklearn.linear_model import LogisticRegression
from pydantic import BaseModel
import joblib
import os
import google.generativeai as genai

load_dotenv()

# === App & Middleware ===
app = FastAPI(title="Vertos AI B2B SaaS Microblogs")
app.add_middleware(SessionMiddleware, secret_key="!secret")

# === OAuth Setup ===
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# === Database Setup ===
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# === Models ===
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    profile_pic = Column(String, nullable=True)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    author = relationship("User", back_populates="posts")
    post_metadata = relationship("PostMetadata", back_populates="post", uselist=False)

class PostMetadata(Base):
    __tablename__ = "post_metadata"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    purpose = Column(String(50))
    target_group = Column(String(100))
    extra = Column(JSON, nullable=True)
    post = relationship("Post", back_populates="post_metadata")

class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))

class Skip(Base):
    __tablename__ = "skips"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))

# === Dependency ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Embedding Model ===
try:
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    raise RuntimeError(f"Failed to load embedding model: {e}")

# === Request Schemas ===
class PostCreate(BaseModel):
    content: str
    purpose: str = None
    target_group: str = None

class PostGenerateRequest(BaseModel):
    industry: str
    niche: str
    role: str
    pain_point: str
    channel: str
    idea: str
    contact_info: str

# === Routes ===
@app.get("/")
def root():
    return {"message": "Visit /login to authenticate"}

@app.get("/login")
async def login(request: Request):
    if "swagger" in str(request.headers.get("user-agent", "")).lower():
        raise HTTPException(status_code=400, detail="OAuth login cannot be initiated from Swagger UI.")
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

from starlette.responses import RedirectResponse

@app.get("/auth/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = await oauth.google.userinfo(token=token)
        name = userinfo.get("name")
        email = userinfo.get("email")

        # Find or create the user
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(name=name, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Store in session
        request.session["user"] = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        }

        return JSONResponse({"message": "Login successful", "user": request.session["user"]})

    except Exception as e:
        # Log or debug here if needed
        return JSONResponse(status_code=400, content={"error": "OAuth callback failed", "detail": str(e)})

@app.get("/test_login")
def test_login(request: Request):
    user = request.session.get("user")
    if user:
        return {"logged_in": True, "user": user}
    return {"logged_in": False, "message": "User not logged in"}


@app.get("/users/me")
def get_my_info(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user", {}).get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    user = db.query(User).filter_by(id=user_id).first()
    return {"id": user.id, "name": user.name, "email": user.email}

@app.post("/posts/")
def create_post(data: PostCreate, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user", {}).get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    post = Post(user_id=user_id, content=data.content)
    db.add(post)
    db.commit()
    db.refresh(post)
    metadata = PostMetadata(post_id=post.id, purpose=data.purpose, target_group=data.target_group)
    db.add(metadata)
    db.commit()
    return {"message": "Post created", "post_id": post.id}

@app.post("/generate_post")
async def generate_post(request: PostGenerateRequest):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        prompt = f"""
You are a B2B marketing assistant writing thought-leadership posts.

Write a professional social media post for:
- Industry: {request.industry}
- Niche: {request.niche}
- Role: {request.role}
- Pain Point: {request.pain_point}
- Preferred Channel: {request.channel}

Core idea: {request.idea}

Instructions:
- Start with a catchy title.
- Then write a short, insightful post (under 300 words).
- Subtly weave in the above details (user selected options) as naturally as possible — don't list them.
- End with a soft CTA including this contact info: {request.contact_info}.
- Keep tone expert, authentic, and relevant to the industry.
Return only the title and post text in markdown format.
"""
        response = model.generate_content(prompt)
        return {"output": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

from fastapi import Query

@app.get("/search")
def search_posts(q: str = Query(..., description="Search query"), db: Session = Depends(get_db)):
    all_posts = db.query(Post).all()
    if not all_posts:
        return {"message": "No posts available for search."}

    query_embedding = embedder.encode(q, convert_to_tensor=True)
    post_texts = [post.content for post in all_posts]
    post_embeddings = embedder.encode(post_texts, convert_to_tensor=True)
    similarities = util.cos_sim(query_embedding, post_embeddings)[0]

    # Pair each post with its similarity score
    indexed_scores = [(idx, float(similarities[idx])) for idx in range(len(all_posts))]

    # Sort by similarity score descending
    top_scored = sorted(indexed_scores, key=lambda x: x[1], reverse=True)[:5]

    results = []
    for idx, score in top_scored:
        post = all_posts[idx]
        author = db.query(User).filter_by(id=post.user_id).first()
        results.append({
            "post_id": post.id,
            "content": post.content,
            "similarity": f"{score * 100:.2f}%",
            "author": author.name,
            "created_at": post.created_at,
        })

    return {"query": q, "results": results}

@app.get("/feed")
def get_feed(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user", {}).get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    user_posts = db.query(Post).filter_by(user_id=user_id).all()
    if not user_posts:
        return {"message": "No posts to base feed on."}
    all_other_posts = db.query(Post).filter(Post.user_id != user_id).all()
    if not all_other_posts:
        return {"message": "No posts from other users"}
    user_post_embeddings = embedder.encode([post.content for post in user_posts], convert_to_tensor=True)
    other_post_embeddings = embedder.encode([post.content for post in all_other_posts], convert_to_tensor=True)
    similarities = util.cos_sim(user_post_embeddings.mean(dim=0), other_post_embeddings)
    sorted_indices = similarities[0].argsort(descending=True)
    feed = []
    for idx in sorted_indices[:10]:
        post = all_other_posts[idx]
        score = float(similarities[0][idx]) * 100
        author = db.query(User).filter_by(id=post.user_id).first()
        feed.append({
            "post_id": post.id,
            "content": post.content,
            "similarity": f"{score:.2f}%",
            "author": author.name,
            "created_at": post.created_at,
        })
    return {"feed": feed}

@app.post("/like/{post_id}")
def like_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user", {}).get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    if db.query(Like).filter_by(user_id=user_id, post_id=post_id).first():
        raise HTTPException(status_code=400, detail="Already liked")
    db.add(Like(user_id=user_id, post_id=post_id))
    db.commit()
    return {"message": "Post liked"}

@app.post("/skip/{post_id}")
def skip_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user", {}).get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    db.add(Skip(user_id=user_id, post_id=post_id))
    db.commit()
    return {"message": "Post skipped"}

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}

@app.on_event("startup")
@repeat_every(seconds=3600)
def train_user_model():
    db = SessionLocal()
    posts = {p.id: p.content for p in db.query(Post).all()}
    likes = db.query(Like).all()
    skips = db.query(Skip).all()
    X, y = [], []
    for l in likes:
        if l.post_id in posts:
            X.append(embedder.encode(posts[l.post_id]))
            y.append(1)
    for s in skips:
        if s.post_id in posts:
            X.append(embedder.encode(posts[s.post_id]))
            y.append(0)
    if len(X) >= 5:
        clf = LogisticRegression()
        clf.fit(X, y)
        joblib.dump(clf, "user_behavior_model.pkl")
    db.close()