1. Open a terminal in the project directory.
2. Create a new virtual environment named `venv`:

   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Run the script as usual:

   ```bash
   python3 python_paste.py
   ```

To deactivate the virtual environment, simply run:

```bash
deactivate
```

This project can also run inside a docker container

```bash
docker-compose up --build
```
## Notes:
Each time the app starts, it will delete pastes that are older than 90 days. This is to help keep the database small and remove any old pastes. You can remove this feature by commenting out `delete_old_pastes()` towards the bottom of `python_paste.py`.