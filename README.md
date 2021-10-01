# Discord Binance Bot
A bot which watches for new signals from a discord channel and place the order on binance with OCO targets.

### Setup Python virtual environment for the project & activate it.
 - Linux
   ```python
   cd discord-binance-bot
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
 - Windows
   ```python
   cd discord-binance-bot
   python -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt
   ```

# Fix, if needed
1. `ImportError: cannot import name 'Client' from 'binance'`

   - Uninstall, Reinstall, Upgrade the package
    ```python
    python -m pip uninstall python-binance
    python -m pip install python-binance
    python -m pip install --upgrade python-binance
    ```