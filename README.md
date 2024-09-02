## Introduction
Simple task runner with a focus on separated contexts and workflows execution across JSON-RPC.
 
### Install
    > git clone https://github.com/GRAYgoose124/dizzy.git
    > cd dizzy 
    > poetry install

### Run
    > poetry run dizzy server
    > poetry run dizzy client


#### On env vars
Use DIZZY_DATA_ROOT to set your data root, which will be populated with /default_data if no `settings.yml` is found. (if not set, will look in ~/.dizzy for settings.yml or use /default_data)
