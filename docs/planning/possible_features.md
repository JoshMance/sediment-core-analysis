# Possible Future Features

## Store / AppController

- **Duplicate core import prevention** — `import_core_from_image` currently allows the same file to be loaded multiple times, creating duplicate entities. Consider rejecting or warning when a `source_file_path` already exists in the Store.
