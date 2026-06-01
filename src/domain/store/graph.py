"""Reserved for future performance optimisation only.

Field-change propagation (e.g. cascading mm_per_px to child cores) is
declared in ``src/domain/entities/propagation.py`` and applied by the
Store's ``update_field`` via BFS traversal over entity attributes.

Do NOT implement cascading features here — add a ``PropagationRule`` in
``propagation.py`` instead.
"""
