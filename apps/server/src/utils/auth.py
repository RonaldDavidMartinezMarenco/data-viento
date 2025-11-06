"""
Authentication Utilities

Provides secure authentication functionality:
- Password hashing using bcrypt
- JWT token generation and validation
- Token payload encoding/decoding

Security Features:
- Passwords are hashed with bcrypt (industry standard)
- JWT tokens with expiration
- Secure token validation
- Never stores plain-text passwords
"""

import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

config_dir = Path(__file__).parent 
env_path = config_dir.parent / '.env'


print(f"Looking for .env at: {env_path}")
print(f".env exists: {env_path.exists()}")

load_dotenv(env_path)

class AuthUtils:
    """
    Utility class for authentication operations
    
    Handles:
    - Password hashing and verification (bcrypt)
    - JWT token creation and validation
    - Token payload management
    """
    
    # JWT Configuration
    # IMPORTANT: Change this secret key in production!
    # Set via environment variable: JWT_SECRET_KEY
    SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    # JWT Algorithm (HS256 is HMAC with SHA-256)
    ALGORITHM = 'HS256'
    
    # Token expiration times
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS = 30    # 30 days
    
    
    # ========================================
    # PASSWORD HASHING (bcrypt)
    # ========================================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain-text password using bcrypt
        
        bcrypt automatically:
        - Generates a random salt
        - Applies multiple rounds of hashing (default: 12)
        - Returns a string containing salt + hash
        
        Args:
            password: Plain-text password to hash
            
        Returns:
            str: Hashed password (bcrypt format)
            
        Example:
            >>> hash_password("MyPassword123")
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS6tKZYGi'
        
        Security:
        - Never store plain-text passwords
        - Each hash is unique (even for same password)
        - Computationally expensive (prevents brute-force)
        """
        # Convert password string to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash password
        # Cost factor = 12 (2^12 = 4096 iterations)
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string (bcrypt returns bytes)
        return hashed.decode('utf-8')
    
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain-text password against a bcrypt hash
        
        bcrypt automatically:
        - Extracts the salt from the hash
        - Hashes the plain password with same salt
        - Compares the results in constant time (prevents timing attacks)
        
        Args:
            plain_password: Plain-text password from user login
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if password matches, False otherwise
            
        Example:
            >>> stored_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS6tKZYGi"
            >>> verify_password("MyPassword123", stored_hash)
            True
            >>> verify_password("WrongPassword", stored_hash)
            False
        
        Security:
        - Uses constant-time comparison (prevents timing attacks)
        - No need to extract/store salt separately
        """
        try:
            # Convert strings to bytes
            password_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            
            # Verify password (constant-time comparison)
            return bcrypt.checkpw(password_bytes, hash_bytes)
        
        except Exception:
            # If any error occurs (invalid hash format, etc.), return False
            return False
    
    
    # ========================================
    # JWT TOKEN MANAGEMENT
    # ========================================
    
    @classmethod
    def create_access_token(
        cls,
        user_id: int,
        username: str,
        user_type: str = 'standard_user',
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token for authenticated user
        
        Token contains:
        - sub (subject): user_id
        - username: username
        - user_type: admin or standard_user
        - exp (expiration): timestamp when token expires
        - iat (issued at): timestamp when token was created
        
        Args:
            user_id: User's unique ID
            username: User's username
            user_type: User role ('admin' or 'standard_user')
            expires_delta: Custom expiration time (optional)
            
        Returns:
            str: Encoded JWT token
            
        Example:
            >>> token = create_access_token(
            ...     user_id=1,
            ...     username="ronald_mendez",
            ...     user_type="standard_user"
            ... )
            >>> print(token)
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
        
        Token Structure:
            Header: {"alg": "HS256", "typ": "JWT"}
            Payload: {"sub": 1, "username": "ronald_mendez", "user_type": "standard_user", "exp": 1699200000, "iat": 1699196400}
            Signature: HMAC-SHA256(header + payload, SECRET_KEY)
        """
        now = datetime.now(timezone.utc)
        # Set expiration time
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Build token payload
        payload = {
            'sub': str(user_id),              # Subject (user ID)
            'username': username,         # Username
            'user_type': user_type,       # User role
            'exp': expire,                # Expiration time
            'iat': now      # Issued at time
        }
        
        # Encode and return token
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        
        # jwt.encode() returns str in newer versions, bytes in older versions
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return token
    
    
    @classmethod
    def create_refresh_token(
        cls,
        user_id: int,
        username: str
    ) -> str:
        """
        Create a JWT refresh token for long-term authentication
        
        Refresh tokens:
        - Last longer than access tokens (30 days vs 1 hour)
        - Used to obtain new access tokens without re-login
        - Should be stored securely (httpOnly cookie)
        
        Args:
            user_id: User's unique ID
            username: User's username
            
        Returns:
            str: Encoded JWT refresh token
            
        Example:
            >>> refresh_token = create_refresh_token(
            ...     user_id=1,
            ...     username="ronald_mendez"
            ... )
        
        Usage Flow:
            1. User logs in → receive access token + refresh token
            2. Access token expires (1 hour) → use refresh token to get new access token
            3. Refresh token expires (30 days) → user must log in again
            
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            'sub': str(user_id),
            'username': username,
            'type': 'refresh',  # Mark as refresh token
            'exp': expire,
            'iat': now
        }
        
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return token
    
    
    @classmethod
    def decode_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token
        
        Validates:
        - Token signature (ensures it wasn't tampered with)
        - Token expiration (ensures it's still valid)
        - Token format (ensures it's a valid JWT)
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Token payload if valid, None if invalid/expired
            
        Example:
            >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            >>> payload = decode_token(token)
            >>> print(payload)
            {
                'sub': 1,
                'username': 'ronald_mendez',
                'user_type': 'standard_user',
                'exp': 1699200000,
                'iat': 1699196400
            }
        
        Returns None if:
        - Token is expired
        - Token signature is invalid
        - Token format is invalid
        """
        
        try:
            print(f"\n🔍 [decode_token] Starting decode...")
            print(f"   Token (first 50): {token[:50]}...")
            print(f"   Token (last 50): ...{token[-50:]}")
            print(f"   Token length: {len(token)}")
            print(f"   SECRET_KEY exists: {cls.SECRET_KEY is not None}")
            print(f"   SECRET_KEY (first 10 chars): {cls.SECRET_KEY[:10] if cls.SECRET_KEY else 'None'}...")
            print(f"   ALGORITHM: {cls.ALGORITHM}")
            
            # Decode and validate token
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM]
            )
            
            print(f"✅ [decode_token] Decode successful!")
            print(f"   Payload: {payload}")
            return payload
        
        except jwt.ExpiredSignatureError as e:
                # Token has expired
                print(f"❌ [decode_token] Token expired: {e}")
                return None
            
        except jwt.InvalidTokenError as e:
                # Token is invalid (bad signature, wrong format, etc.)
                print(f"❌ [decode_token] Invalid token: {e}")
                return None
            
        except Exception as e:
                # Any other error
                print(f"💥 [decode_token] Unexpected error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return None
            
    
    @classmethod
    def verify_token(cls, token: str) -> bool:
        """
        Verify if a token is valid (not expired, correct signature)
        
        Args:
            token: JWT token string
            
        Returns:
            bool: True if token is valid, False otherwise
            
        Example:
            >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            >>> if verify_token(token):
            ...     print("Token is valid")
            ... else:
            ...     print("Token is invalid or expired")
        """
        return cls.decode_token(token) is not None
    
    
    @classmethod
    def get_user_from_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Extract user information from a valid token
        
        Args:
            token: JWT token string
            
        Returns:
            dict: User info from token (user_id, username, user_type) or None
            
        Example:
            >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            >>> user_info = get_user_from_token(token)
            >>> print(user_info)
            {
                'user_id': 1,
                'username': 'ronald_mendez',
                'user_type': 'standard_user'
            }
        
        Usage in API routes:
            >>> # Get token from Authorization header
            >>> token = request.headers.get('Authorization', '').replace('Bearer ', '')
            >>> user_info = AuthUtils.get_user_from_token(token)
            >>> if user_info:
            ...     # User is authenticated
            ...     user_id = user_info['user_id']
            ... else:
            ...     # Invalid/expired token
            ...     return {"error": "Unauthorized"}, 401
        """
        payload = cls.decode_token(token)
        
        if not payload:
            return None
        
        user_id_str = payload.get('sub')
        
        try:
            user_id = int(user_id_str)  
        except (ValueError, TypeError):
             return None  
        
        
        return {
            'user_id': user_id,
            'username': payload.get('username'),
            'user_type': payload.get('user_type', 'standard_user')
        }
    
    
    @classmethod
    def is_token_expired(cls, token: str) -> bool:
        """
        Check if a token is expired
        
        Args:
            token: JWT token string
            
        Returns:
            bool: True if token is expired, False if still valid
            
        Example:
            >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            >>> if is_token_expired(token):
            ...     print("Please log in again")
        """
        try:
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM]
            )
            # If decode succeeds, token is not expired
            return False
        
        except jwt.ExpiredSignatureError:
            # Token has expired
            return True
        
        except Exception:
            # Invalid token (treat as expired)
            return True
    
    
    @classmethod
    def get_token_expiration(cls, token: str) -> Optional[datetime]:
        """
        Get the expiration datetime of a token
        
        Args:
            token: JWT token string
            
        Returns:
            datetime: Token expiration time or None if invalid
            
        Example:
            >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            >>> exp_time = get_token_expiration(token)
            >>> print(f"Token expires at: {exp_time}")
            Token expires at: 2024-11-05 17:00:00
        """
        payload = cls.decode_token(token)
        
        if not payload or 'exp' not in payload:
            return None
        
        # Convert Unix timestamp to datetime
        return datetime.fromtimestamp(payload['exp'], tz = timezone.utc)
    
    
    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> Optional[str]:
        """
        Generate a new access token using a refresh token
        
        Validates the refresh token and creates a new access token
        without requiring the user to log in again.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            str: New access token or None if refresh token is invalid
            
        Example:
            >>> refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            >>> new_access_token = refresh_access_token(refresh_token)
            >>> if new_access_token:
            ...     print("New access token generated")
            ... else:
            ...     print("Please log in again")
        
        Usage Flow:
            1. Access token expires (401 Unauthorized)
            2. Client sends refresh token to /api/auth/refresh
            3. Server validates refresh token
            4. Server generates new access token
            5. Client uses new access token
        """
        payload = cls.decode_token(refresh_token)
        
        if not payload:
            return None
        
        # Verify it's a refresh token
        if payload.get('type') != 'refresh':
            return None
        
        user_id_str = payload.get('sub')
        try:
            user_id = int(user_id_str)  
        except (ValueError, TypeError):
            return None
        
        # Create new access token with same user info
        return cls.create_access_token(
            user_id=user_id,
            username=payload.get('username'),
            user_type=payload.get('user_type', 'standard_user')
        )


# ========================================
# UTILITY FUNCTIONS (for easy import)
# ========================================

def hash_password(password: str) -> str:
    """Shorthand for AuthUtils.hash_password()"""
    return AuthUtils.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Shorthand for AuthUtils.verify_password()"""
    return AuthUtils.verify_password(plain_password, hashed_password)


def create_access_token(user_id: int, username: str, user_type: str = 'standard_user') -> str:
    """Shorthand for AuthUtils.create_access_token()"""
    return AuthUtils.create_access_token(user_id, username, user_type)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Shorthand for AuthUtils.decode_token()"""
    return AuthUtils.decode_token(token)


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Shorthand for AuthUtils.get_user_from_token()"""
    return AuthUtils.get_user_from_token(token)


