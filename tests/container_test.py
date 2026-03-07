"""
Manual test for EntityContainer — passive CRUD bucket

Exercises all container operations in isolation (no Qt required).
Prints results directly to stdout for quick verification.

Run with: python -m tests.container_test
"""
from pathlib import Path

from src.domain.entities.image_entity import ImageEntity
from src.domain.store.container import EntityContainer


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def ok(label: str, value: object = "") -> None:
    print(f"  ✓ {label}  {value}")


def fail(label: str, err: Exception) -> None:
    print(f"  ✗ {label}  → {type(err).__name__}: {err}")


def main():
    c = EntityContainer()

    # ── Add ─────────────────────────────────────────────────
    section("add — basic")
    img = ImageEntity(name="photo.png", file_path=Path("/tmp/photo.png"))
    eid = c.add(img)
    ok("returns id", eid)
    ok("id assigned on entity", img.id == eid)
    ok("count is 1", c.count())

    section("add — auto-id when None")
    img2 = ImageEntity(name="scan.tif")
    eid2 = c.add(img2)
    ok("id generated", eid2)
    ok("count is 2", c.count())

    section("add — duplicate id raises ValueError")
    dup = ImageEntity(name="dup.png", id=eid)
    try:
        c.add(dup)
        fail("should have raised", RuntimeError("no error"))
    except ValueError as e:
        ok("ValueError", e)

    section("add — unregistered type raises TypeError")
    try:
        c.add({"name": "not an entity"})
        fail("should have raised", RuntimeError("no error"))
    except TypeError as e:
        ok("TypeError", e)

    # ── Read ────────────────────────────────────────────────
    section("get")
    ok("found by id", c.get(eid).name)
    ok("missing id → None", c.get("nonexistent") is None)

    section("get_many")
    result = c.get_many([eid, eid2, "missing"])
    ok("returns 2 (skips missing)", len(result))

    section("get_field")
    ok("name field", c.get_field(eid, "name"))
    ok("file_path field", c.get_field(eid, "file_path"))
    ok("missing entity → None", c.get_field("nope", "name") is None)
    ok("missing field → None", c.get_field(eid, "bogus") is None)

    section("list_entities — all")
    all_entities = c.list_entities()
    ok("count", len(all_entities))

    section("list_entities — by type")
    typed = c.list_entities(entity_type="ImageEntity")
    ok("ImageEntity count", len(typed))

    section("list_entities — include_ids")
    pairs = c.list_entities(include_ids=True)
    ok("returns (id, entity) tuples", [(eid, e.name) for eid, e in pairs])

    # ── Update ──────────────────────────────────────────────
    section("update_field")
    c.update_field(eid, "name", "renamed.png")
    ok("name updated", c.get(eid).name)

    section("update_field — bad entity raises KeyError")
    try:
        c.update_field("nope", "name", "x")
        fail("should have raised", RuntimeError("no error"))
    except KeyError as e:
        ok("KeyError", e)

    section("update_field — bad field raises AttributeError")
    try:
        c.update_field(eid, "nonexistent_field", "x")
        fail("should have raised", RuntimeError("no error"))
    except AttributeError as e:
        ok("AttributeError", e)

    # ── Stats ───────────────────────────────────────────────
    section("count + summary")
    ok("total count", c.count())
    ok("typed count", c.count("ImageEntity"))
    ok("summary", c.summary())

    # ── Remove ──────────────────────────────────────────────
    section("remove")
    removed = c.remove(eid)
    ok("returns removed entity", removed.name)
    ok("count after remove", c.count())
    ok("get after remove → None", c.get(eid) is None)

    section("remove — missing id raises KeyError")
    try:
        c.remove("already_gone")
        fail("should have raised", RuntimeError("no error"))
    except KeyError as e:
        ok("KeyError", e)

    # ── Clear ───────────────────────────────────────────────
    section("clear")
    c.clear()
    ok("count after clear", c.count())
    ok("summary after clear", c.summary())

    # ── Done ────────────────────────────────────────────────
    section("ALL CONTAINER TESTS PASSED")


if __name__ == "__main__":
    main()
