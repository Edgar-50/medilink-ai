import argparse
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.user import User, UserRole
import app.models

parser=argparse.ArgumentParser(description="Create or promote a MediLink administrator")
parser.add_argument("--email",required=True)
parser.add_argument("--name",default="MediLink Administrator")
parser.add_argument("--password",required=True)
args=parser.parse_args()
Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    email=args.email.lower().strip()
    user=db.query(User).filter(User.email==email).first()
    if user:
        user.role=UserRole.admin
        user.hashed_password=hash_password(args.password)
        user.full_name=args.name
        user.is_active=True
        print(f"Promoted {email} to administrator")
    else:
        db.add(User(full_name=args.name,email=email,hashed_password=hash_password(args.password),role=UserRole.admin,is_active=True))
        print(f"Created administrator {email}")
    db.commit()
finally:
    db.close()
