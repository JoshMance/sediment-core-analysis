"""
Runtime panel views — created on demand, not at startup.

Rule: This package is ONLY for views that are created at runtime (e.g. when
the user opens an entity). Views that exist on application startup and persist
for its lifetime belong in src/ui/views/shell/ instead.

Examples of what belongs here:
  - A canvas/editor panel opened when the user double-clicks an entity
  - A detail view shown when an entity is selected

Examples of what does NOT belong here (they live in shell/):
  - VariablesList — always present in the shell
"""
