# Discord Binance Bot
A bot which watches for new signals from any discord channel and place the order on binance with OCO targets.

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

### Configurations

- Create a copy of `config.example.json` and rename it to `config.json`
- Replace all <KEYS> with appropriate values.