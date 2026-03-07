# Possible Future Features

## Store / AppController

- **Duplicate entity prevention** — `create_image_entity` currently allows the same file to be loaded multiple times, creating duplicate entities. Consider rejecting or warning when a `file_path` already exists in the Store.
