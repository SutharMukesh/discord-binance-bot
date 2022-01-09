# Discord Binance Script

A script which reads signals from any discord channel and place the order on binance with OCO targets.

### Features

- Supports reading message from multple servers, channels and authors
- Flexible message/signal parsing from author 
  - Check `message_templates` from `config.example.json`
- Support for discord bot which sends notification regarding all script process.

### Configuration

- Create a copy of `config.example.json` and rename it to `config.json`
- Replace all `<KEYS>` with appropriate values.

### Getting Started

- **Setup**
    - Install python requirements
    - `pip install -r requirements.txt`

- **start**
    - `python scheduler.py`