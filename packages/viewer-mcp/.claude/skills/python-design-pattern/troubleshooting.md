# Troubleshooting

Common design dilemmas and how to resolve them.

## A class is growing and seems to have multiple responsibilities, but splitting it feels wrong

Apply the "reason to change" test: list every change that could require editing this class. If the list has items from different domains (e.g., HTTP parsing AND business rules AND formatting), split it. If all changes stem from the same domain concern, the class may be appropriately sized.

## Injecting all dependencies through the constructor is producing constructors with 7+ parameters

This is a sign of too many responsibilities in one class, not a problem with dependency injection. Split the class into smaller units first, then each constructor naturally becomes smaller.

## Composition is producing deeply nested wrapper objects that are hard to trace

Keep the composition shallow (2-3 levels). If wrapping is the only mechanism, consider whether a Protocol-based approach or simple function composition would be cleaner than a chain of decorator objects.

## The rule of three says not to abstract yet, but the duplication is causing bugs when one copy is updated but not the other

Duplication that diverges in dangerous ways should be abstracted sooner. The rule of three is a heuristic, not a law. If the copies are already diverging incorrectly, extract immediately and add a test that exercises the shared behavior.

## A service layer is importing from the API layer, breaking the dependency direction

This is a layering violation. The service layer must not import from handlers. Introduce a shared types/models layer that both can import from, keeping the dependency arrow pointing downward (API → Service → Repository).
