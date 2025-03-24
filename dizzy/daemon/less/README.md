# Daemon/Less

```bash
$ cd dizzy
$ cat demo/requests/new_project.json | jq | dizzyless --protocol-dir "$(pwd)/demo/custom_data" | jq
```