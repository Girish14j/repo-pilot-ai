"""
The authoritative knowledge we give our agents.

Each entry is a document with:
- content: the actual text the LLM will read
- metadata: tags so we can filter by topic when searching

We write these manually because we want full control over quality.
These are not scraped — they are curated engineering knowledge.
"""

KNOWLEDGE_BASE = [

    # ─── SOLID Principles ─────────────────────────────────────────────────────

    {
        "content": """Single Responsibility Principle (SRP):
A class or module should have only one reason to change.
This means each class should do exactly one thing and do it well.

Violations to look for in code:
- Classes named with 'And' (UserAuthAndEmailSender) — doing two things
- Functions longer than 20-30 lines — likely doing too much
- Files mixing database logic with business logic with HTTP handling
- God classes that know about everything in the system

Good example: UserRepository (only handles DB), EmailService (only sends email)
Bad example: UserManager (handles auth, email, DB, validation, logging)""",
        "metadata": {"topic": "solid", "principle": "SRP"}
    },

    {
        "content": """Open/Closed Principle (OCP):
Software entities should be open for extension but closed for modification.
You should be able to add new behavior without changing existing code.

Violations to look for:
- Long if/elif chains that check object types
- Switch statements on type fields
- Adding new features requires editing existing working code
- No use of interfaces, abstract classes, or plugins

Good example: Adding a new payment method by creating a new class that implements PaymentProvider
Bad example: Adding a new payment method by adding another elif to process_payment()""",
        "metadata": {"topic": "solid", "principle": "OCP"}
    },

    {
        "content": """Liskov Substitution Principle (LSP):
Subtypes must be substitutable for their base types without breaking the program.
If class B extends class A, you should be able to use B anywhere A is expected.

Violations to look for:
- Subclasses that override methods to throw NotImplementedError
- Subclasses that weaken preconditions or strengthen postconditions
- Inheritance used for code reuse rather than true IS-A relationships
- Type checking with isinstance() throughout the codebase

Good example: Square and Rectangle both implement Shape correctly
Bad example: Square extends Rectangle but breaks setWidth() behavior""",
        "metadata": {"topic": "solid", "principle": "LSP"}
    },

    {
        "content": """Interface Segregation Principle (ISP):
Clients should not be forced to depend on interfaces they do not use.
Many specific interfaces are better than one general-purpose interface.

Violations to look for:
- Large abstract base classes with many methods
- Classes that implement an interface but leave many methods as 'pass' or raise NotImplementedError
- One massive service class that every part of the system imports
- Fat interfaces that combine unrelated operations

Good example: ReadableRepository and WritableRepository as separate interfaces
Bad example: One Repository interface with 20 methods that most clients don't need""",
        "metadata": {"topic": "solid", "principle": "ISP"}
    },

    {
        "content": """Dependency Inversion Principle (DIP):
High-level modules should not depend on low-level modules.
Both should depend on abstractions (interfaces/abstract classes).

Violations to look for:
- Direct instantiation of dependencies inside classes (new MyService() inside another service)
- No dependency injection — classes create their own dependencies
- High-level business logic imports specific database or HTTP implementations
- Hard to test because dependencies can't be swapped with mocks

Good example: UserService receives a UserRepository interface via constructor injection
Bad example: UserService creates PostgresUserRepository() directly inside __init__""",
        "metadata": {"topic": "solid", "principle": "DIP"}
    },

    # ─── Clean Architecture ────────────────────────────────────────────────────

    {
        "content": """Clean Architecture - Layer Separation:
Robert Martin's Clean Architecture defines concentric layers:
1. Entities (innermost) — core business objects and rules
2. Use Cases — application-specific business logic
3. Interface Adapters — controllers, presenters, gateways
4. Frameworks & Drivers (outermost) — databases, web frameworks, UI

The Dependency Rule: source code dependencies must point inward only.
Inner layers know nothing about outer layers.

Signs of good layer separation in a project:
- models/ or entities/ folder separate from routers/ or controllers/
- services/ folder containing business logic separate from HTTP handling
- database logic isolated in repositories/ folder
- No ORM models imported directly into route handlers""",
        "metadata": {"topic": "clean_architecture", "principle": "layers"}
    },

    {
        "content": """Clean Architecture - Folder Structure Best Practices:
A well-structured Python/FastAPI project should look like:

app/
├── models/          # Pydantic schemas and domain entities
├── services/        # Business logic — knows nothing about HTTP
├── repositories/    # Database access — knows nothing about business logic  
├── routers/         # HTTP handlers — thin layer, calls services only
├── core/            # Config, security, shared utilities
└── main.py          # App entry point, wires everything together

Red flags in folder structure:
- All code in main.py or a single file
- No separation between HTTP layer and business logic
- Database queries directly in route handlers
- No models or schema definitions
- Flat structure with no organization""",
        "metadata": {"topic": "clean_architecture", "principle": "structure"}
    },

    # ─── OWASP Top 10 ─────────────────────────────────────────────────────────

    {
        "content": """OWASP A01:2021 - Broken Access Control:
The most critical web application security risk.

What it means: Users can act outside their intended permissions.

Signs to look for in code:
- No authorization checks before sensitive operations
- JWT tokens created but never validated for permissions
- Missing role-based access control (RBAC)
- API endpoints that don't verify the requesting user owns the resource
- Directory traversal vulnerabilities (using user input in file paths)
- CORS misconfiguration — allow_origins=["*"] in production
- Missing rate limiting on sensitive endpoints (login, password reset)

Example vulnerable pattern:
@app.get("/user/{user_id}/data")
def get_data(user_id: int):
    return db.get_user_data(user_id)  # No check: does caller own this user_id?""",
        "metadata": {"topic": "owasp", "category": "A01", "risk": "access_control"}
    },

    {
        "content": """OWASP A02:2021 - Cryptographic Failures:
Failures related to cryptography that expose sensitive data.

Signs to look for in code:
- Passwords stored in plain text or using MD5/SHA1 (use bcrypt/argon2)
- Sensitive data in URL parameters (tokens, passwords in GET requests)
- HTTP used instead of HTTPS for sensitive data
- Hardcoded secrets, API keys, or passwords in source code
- Weak random number generation for tokens (use secrets module, not random)
- JWT with algorithm set to 'none'
- Encryption keys hardcoded in the codebase

Critical check: Search for any .env files committed to the repository.
Search for patterns like: password = "hardcoded", api_key = "sk-..."
Any secrets in code — even in comments — are a critical vulnerability.""",
        "metadata": {"topic": "owasp", "category": "A02", "risk": "cryptography"}
    },

    {
        "content": """OWASP A03:2021 - Injection:
Injection flaws occur when untrusted data is sent to an interpreter.

Types to look for:
- SQL Injection: string formatting in SQL queries instead of parameterized queries
- Command Injection: os.system() or subprocess with user input
- LDAP Injection, XPath Injection, NoSQL Injection

Vulnerable patterns in Python:
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # VULNERABLE
os.system(f"ls {user_provided_path}")  # VULNERABLE

Safe patterns:
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))  # SAFE
subprocess.run(["ls", user_provided_path], shell=False)  # SAFER

For ORMs: raw query methods like .raw() or text() with user input are still vulnerable.
Always use parameterized queries or ORM query builders.""",
        "metadata": {"topic": "owasp", "category": "A03", "risk": "injection"}
    },

    {
        "content": """OWASP A05:2021 - Security Misconfiguration:
Insecure default configurations, incomplete configurations, or misconfigured cloud services.

Signs to look for in code and config files:
- Debug mode enabled in production (DEBUG=True, reload=True hardcoded)
- Default credentials not changed
- Unnecessary features enabled (unused API endpoints, services)
- Stack traces exposed to end users in error responses
- Missing security headers (CORS too permissive)
- Verbose error messages that reveal implementation details
- Development dependencies in production requirements

FastAPI specific:
- Swagger UI (/docs) exposed in production without authentication
- Exception handlers that return full stack traces to clients
- allow_origins=["*"] with allow_credentials=True (this is actually blocked by browsers but shows intent)""",
        "metadata": {"topic": "owasp", "category": "A05", "risk": "misconfiguration"}
    },

    {
        "content": """OWASP A07:2021 - Identification and Authentication Failures:
Weaknesses in authentication and session management.

Signs to look for:
- No rate limiting on login endpoints (allows brute force)
- Weak password policies not enforced
- Session tokens that don't expire
- JWT tokens with very long expiration (exp claim)
- No multi-factor authentication for sensitive operations
- Passwords visible in logs
- Insecure password reset flows (predictable tokens)
- Missing account lockout after failed attempts

Python/FastAPI patterns to flag:
- No slowapi or similar rate limiting middleware
- JWT decode without verifying expiration
- Tokens stored in localStorage (vulnerable to XSS) vs httpOnly cookies
- No refresh token rotation strategy""",
        "metadata": {"topic": "owasp", "category": "A07", "risk": "authentication"}
    },

    # ─── Documentation Best Practices ─────────────────────────────────────────

    {
        "content": """README Best Practices for Software Projects:
A professional README should contain these sections in order:

1. Project Title and Description (what it does in 2 sentences)
2. Badges (build status, coverage, version, license)
3. Demo or Screenshot (show don't tell)
4. Features list (bullet points of key capabilities)
5. Tech Stack (what technologies are used and why)
6. Prerequisites (what needs to be installed first)
7. Installation (step by step, copy-pasteable commands)
8. Environment Variables (list all required .env variables with examples)
9. Usage / How to Run (development and production)
10. API Documentation (link to Swagger or list endpoints)
11. Project Structure (folder tree with explanations)
12. Contributing Guidelines
13. License

Common README failures:
- Missing installation instructions
- No environment variable documentation
- No screenshots or demo
- Installation steps that don't work
- No explanation of what the project actually does
- Missing license""",
        "metadata": {"topic": "documentation", "type": "readme"}
    },

    {
        "content": """API Documentation Best Practices:
Well-documented APIs are critical for maintainability and adoption.

FastAPI specific best practices:
- Every endpoint should have a docstring describing what it does
- Use response_model to document the response structure
- Use tags to group related endpoints
- Add example values to Pydantic models using Field(example=...)
- Document error responses with responses parameter
- Version your API (/api/v1/) from day one
- Use meaningful operation IDs

General API documentation rules:
- Every endpoint documents: purpose, parameters, request body, response, errors
- Authentication requirements clearly stated
- Rate limits documented
- Breaking changes versioned, not made in place
- Provide working example requests (curl or Postman collection)""",
        "metadata": {"topic": "documentation", "type": "api"}
    },
]