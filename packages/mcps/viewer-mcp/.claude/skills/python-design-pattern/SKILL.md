---
name: python-design-patterns
description: Python design patterns and anti-patterns. Use when designing new components, refactoring, reviewing code for common mistakes, choosing abstractions, or evaluating pull requests for structural issues like tight coupling, leaking internal types, or error handling problems.
---

# Python Design Patterns

Write maintainable Python code using fundamental design principles. These patterns help you build systems that are easy to understand, test, and modify.

## When to Use This Skill

- Designing new components or services
- Refactoring complex or tangled code
- Deciding whether to create an abstraction
- Choosing between inheritance and composition
- Evaluating code complexity and coupling
- Planning modular architectures
- Reviewing code before merge (anti-patterns checklist)
- Debugging issues that might stem from known bad practices

## Core Concepts

1. **KISS** — simplest solution that works; complexity must be justified
2. **Single Responsibility** — each unit has one reason to change
3. **Composition over Inheritance** — combine objects, don't extend classes
4. **High Cohesion, Low Coupling** — modules do one thing well; changes don't ripple
5. **Rule of Three** — wait for three instances before abstracting

## Fundamental Patterns

### Pattern 1: KISS - Keep It Simple

Before adding complexity, ask: does a simpler solution work?

```python
# Over-engineered: Factory with registration
class OutputFormatterFactory:
    _formatters: dict[str, type[Formatter]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(formatter_cls):
            cls._formatters[name] = formatter_cls
            return formatter_cls
        return decorator

    @classmethod
    def create(cls, name: str) -> Formatter:
        return cls._formatters[name]()

@OutputFormatterFactory.register("json")
class JsonFormatter(Formatter):
    ...

# Simple: Just use a dictionary
FORMATTERS = {
    "json": JsonFormatter,
    "csv": CsvFormatter,
    "xml": XmlFormatter,
}

def get_formatter(name: str) -> Formatter:
    """Get formatter by name."""
    if name not in FORMATTERS:
        raise ValueError(f"Unknown format: {name}")
    return FORMATTERS[name]()
```

The factory pattern adds code without adding value here. Save patterns for when they solve real problems.

### Pattern 2: Single Responsibility Principle

Each class or function should have one reason to change.

```python
# BAD: Handler does everything
class UserHandler:
    async def create_user(self, request: Request) -> Response:
        # HTTP parsing
        data = await request.json()

        # Validation
        if not data.get("email"):
            return Response({"error": "email required"}, status=400)

        # Database access
        user = await db.execute(
            "INSERT INTO users (email, name) VALUES ($1, $2) RETURNING *",
            data["email"], data["name"]
        )

        # Response formatting
        return Response({"id": user.id, "email": user.email}, status=201)

# GOOD: Separated concerns
class UserService:
    """Business logic only."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def create_user(self, data: CreateUserInput) -> User:
        # Only business rules here
        user = User(email=data.email, name=data.name)
        return await self._repo.save(user)

class UserHandler:
    """HTTP concerns only."""

    def __init__(self, service: UserService) -> None:
        self._service = service

    async def create_user(self, request: Request) -> Response:
        data = CreateUserInput(**(await request.json()))
        user = await self._service.create_user(data)
        return Response(user.to_dict(), status=201)
```

Now HTTP changes don't affect business logic, and vice versa.

### Pattern 3: Separation of Concerns

Organize code into distinct layers with clear responsibilities.

```
┌─────────────────────────────────────────────────────┐
│  API Layer (handlers)                                │
│  - Parse requests                                    │
│  - Call services                                     │
│  - Format responses                                  │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Service Layer (business logic)                      │
│  - Domain rules and validation                       │
│  - Orchestrate operations                            │
│  - Pure functions where possible                     │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Repository Layer (data access)                      │
│  - SQL queries                                       │
│  - External API calls                                │
│  - Cache operations                                  │
└─────────────────────────────────────────────────────┘
```

Each layer depends only on layers below it:

```python
# Repository: Data access
class UserRepository:
    async def get_by_id(self, user_id: str) -> User | None:
        row = await self._db.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        return User(**row) if row else None

# Service: Business logic
class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def get_user(self, user_id: str) -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

# Handler: HTTP concerns
@app.get("/users/{user_id}")
async def get_user(user_id: str) -> UserResponse:
    user = await user_service.get_user(user_id)
    return UserResponse.from_user(user)
```

### Pattern 4: Composition Over Inheritance

Build behavior by combining objects rather than inheriting.

```python
# Inheritance: Rigid and hard to test
class EmailNotificationService(NotificationService):
    def __init__(self):
        super().__init__()
        self._smtp = SmtpClient()  # Hard to mock

    def notify(self, user: User, message: str) -> None:
        self._smtp.send(user.email, message)

# Composition: Flexible and testable
class NotificationService:
    """Send notifications via multiple channels."""

    def __init__(
        self,
        email_sender: EmailSender,
        sms_sender: SmsSender | None = None,
        push_sender: PushSender | None = None,
    ) -> None:
        self._email = email_sender
        self._sms = sms_sender
        self._push = push_sender

    async def notify(
        self,
        user: User,
        message: str,
        channels: set[str] | None = None,
    ) -> None:
        channels = channels or {"email"}

        if "email" in channels:
            await self._email.send(user.email, message)

        if "sms" in channels and self._sms and user.phone:
            await self._sms.send(user.phone, message)

        if "push" in channels and self._push and user.device_token:
            await self._push.send(user.device_token, message)

# Easy to test with fakes
service = NotificationService(
    email_sender=FakeEmailSender(),
    sms_sender=FakeSmsSender(),
)
```

## Advanced Patterns

### Pattern 5: Rule of Three

Wait until you have three instances before abstracting.

```python
# Two similar functions? Don't abstract yet
def process_orders(orders: list[Order]) -> list[Result]:
    results = []
    for order in orders:
        validated = validate_order(order)
        result = process_validated_order(validated)
        results.append(result)
    return results

def process_returns(returns: list[Return]) -> list[Result]:
    results = []
    for ret in returns:
        validated = validate_return(ret)
        result = process_validated_return(validated)
        results.append(result)
    return results

# These look similar, but wait! Are they actually the same?
# Different validation, different processing, different errors...
# Duplication is often better than the wrong abstraction

# Only after a third case, consider if there's a real pattern
# But even then, sometimes explicit is better than abstract
```

### Pattern 6: Function Size Guidelines

Keep functions focused. Extract when a function:

- Exceeds 20-50 lines (varies by complexity)
- Serves multiple distinct purposes
- Has deeply nested logic (3+ levels)

```python
# Too long, multiple concerns mixed
def process_order(order: Order) -> Result:
    # 50 lines of validation...
    # 30 lines of inventory check...
    # 40 lines of payment processing...
    # 20 lines of notification...
    pass

# Better: Composed from focused functions
def process_order(order: Order) -> Result:
    """Process a customer order through the complete workflow."""
    validate_order(order)
    reserve_inventory(order)
    payment_result = charge_payment(order)
    send_confirmation(order, payment_result)
    return Result(success=True, order_id=order.id)
```

### Pattern 7: Guard Clauses (Early Returns)

Eliminate deep nesting by handling edge cases and errors first, then proceeding with the happy path.

```python
# BAD: Deeply nested — hard to follow the happy path
def process_order(order: Order) -> Result:
    if order is not None:
        if order.status == "pending":
            if order.items:
                if order.payment_method:
                    # Finally the actual logic, 4 levels deep
                    total = sum(item.price for item in order.items)
                    charge(order.payment_method, total)
                    return Result(success=True)
                else:
                    return Result(error="No payment method")
            else:
                return Result(error="No items")
        else:
            return Result(error="Order not pending")
    else:
        return Result(error="No order")

# GOOD: Guard clauses — reject early, happy path stays flat
def process_order(order: Order) -> Result:
    if order is None:
        return Result(error="No order")
    if order.status != "pending":
        return Result(error="Order not pending")
    if not order.items:
        return Result(error="No items")
    if not order.payment_method:
        return Result(error="No payment method")

    # Happy path — no nesting
    total = sum(item.price for item in order.items)
    charge(order.payment_method, total)
    return Result(success=True)
```

Guard clauses work the same way with exceptions:

```python
def get_user(user_id: str) -> User:
    if not user_id:
        raise ValueError("user_id is required")
    if not user_id.startswith("usr_"):
        raise ValueError(f"Invalid user_id format: {user_id}")

    # Happy path
    return repo.get_by_id(user_id)
```

**When to use guard clauses:**
- Validating function inputs
- Checking preconditions before expensive operations
- Handling error/edge cases that short-circuit the function
- Any time you find yourself nesting `if/else` more than 2 levels deep

### Pattern 8: Dependency Injection

Pass dependencies through constructors for testability.

```python
from typing import Protocol

class Logger(Protocol):
    def info(self, msg: str, **kwargs) -> None: ...
    def error(self, msg: str, **kwargs) -> None: ...

class Cache(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int) -> None: ...

class UserService:
    """Service with injected dependencies."""

    def __init__(
        self,
        repository: UserRepository,
        cache: Cache,
        logger: Logger,
    ) -> None:
        self._repo = repository
        self._cache = cache
        self._logger = logger

    async def get_user(self, user_id: str) -> User:
        # Check cache first
        cached = await self._cache.get(f"user:{user_id}")
        if cached:
            self._logger.info("Cache hit", user_id=user_id)
            return User.from_json(cached)

        # Fetch from database
        user = await self._repo.get_by_id(user_id)
        if user:
            await self._cache.set(f"user:{user_id}", user.to_json(), ttl=300)

        return user

# Production
service = UserService(
    repository=PostgresUserRepository(db),
    cache=RedisCache(redis),
    logger=StructlogLogger(),
)

# Testing
service = UserService(
    repository=InMemoryUserRepository(),
    cache=FakeCache(),
    logger=NullLogger(),
)
```

### Pattern 9: Tell, Don't Ask

Objects should do things, not just report data. Move logic to the object that owns the data.

```python
# BAD: Interrogating the object, then acting externally
if cart.total_price() > user.credit:
    raise InsufficientCreditError()
else:
    user.debit(cart.total_price())

# GOOD: Tell the object what to do
cart.checkout(user)

# Inside Cart:
class Cart:
    def checkout(self, user: User) -> None:
        if self.total_price() > user.credit:
            raise InsufficientCreditError()
        user.debit(self.total_price())
```

This keeps logic co-located with the data it operates on. If you find yourself calling `obj.get_x()` then making decisions based on that value, consider moving the decision into the object itself.

### Pattern 10: Replace Comments with Functions

If a condition or expression needs a comment to explain it, extract it into a named function instead.

```python
# BAD: Comment explains a complex condition
# Check if user is eligible for premium features
if user.age > 18 and user.subscription == "active" and not user.is_banned:
    grant_access(user)

# GOOD: Function name IS the documentation
def is_eligible_for_premium(user: User) -> bool:
    return user.age > 18 and user.subscription == "active" and not user.is_banned

if is_eligible_for_premium(user):
    grant_access(user)
```

Comments can go stale. Function names are verified by usage.

### Pattern 11: Eliminate Boolean Arguments

Boolean parameters hide meaning at the call site.

```python
# BAD: What does True mean here?
generate_report(data, True)

def generate_report(data: list, include_summary: bool = False):
    ...

# GOOD: Separate named functions with clear intent
def generate_full_report(data: list): ...
def generate_basic_report(data: list): ...
```

If a boolean parameter controls which branch of a function runs, the function is doing two things (violating SRP). Split it.

## Anti-Patterns

For the full anti-patterns checklist with code examples and quick reference table, see [anti-patterns.md](anti-patterns.md).

Covers: exposed internal types, scattered retry logic, double retry, hard-coded config, bare exceptions, ignored partial failures, missing validation, unclosed resources, blocking in async, missing type hints, happy-path-only testing, and over-mocking.

## Refactoring Safely

**Always write tests before refactoring.** Tests are your safety net — they prove the code works before you touch it and catch regressions as you change it.

```python
# Step 1: Write tests that lock in current behavior
def test_calculate_discount_loyal_customer():
    assert calculate_discount(orders=15) == 0.15

def test_calculate_discount_new_customer():
    assert calculate_discount(orders=2) == 0.0

# Step 2: Run tests — they must pass BEFORE you refactor
# Step 3: Refactor with confidence — tests catch breakage immediately
# Step 4: Run tests again — green means you didn't break anything
```

If the code has no tests and you're about to refactor it, write characterization tests first: tests that capture what the code *currently does*, even if you're not sure it's correct. The goal is to detect unintended changes, not to validate correctness.

```python
# Characterization test: "I don't know if this is right,
# but this is what it does today"
def test_legacy_pricing_current_behavior():
    result = legacy_calculate_price(item="widget", qty=3, region="EU")
    assert result == 47.85  # Captured from current output
```

Once tests are green, refactor freely. If a test breaks, you know exactly what changed.

## Best Practices Summary

1. **Keep it simple** - Choose the simplest solution that works
2. **Single responsibility** - Each unit has one reason to change
3. **Separate concerns** - Distinct layers with clear purposes
4. **Compose, don't inherit** - Combine objects for flexibility
5. **Rule of three** - Wait before abstracting
6. **Keep functions small** - 20-50 lines (varies by complexity), one purpose
7. **Inject dependencies** - Constructor injection for testability
8. **Test before refactoring** - Lock in behavior with tests, then change safely
9. **Delete before abstracting** - Remove dead code, then consider patterns
10. **Explicit over clever** - Readable code beats elegant code

## Troubleshooting

For common design dilemmas (growing classes, too many constructor params, composition depth, when to break the rule of three, layering violations), see [troubleshooting.md](troubleshooting.md).

## Related Skills

- **testing-python** — Test each layer in isolation using the dependency injection structure established here
- **python-type-safety** — Type hints, generics, protocols, and strict type checking