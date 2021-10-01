# Discord Binance Bot
A bot which watches for new signals from a discord channel and place the order on binance with OCO targets.


# Fix, if needed
1. `ImportError: cannot import name 'Client' from 'binance'`

   - Uninstall, Reinstall, Upgrade the package
    ```python
    python -m pip uninstall python-binance
    python -m pip install python-binance
    python -m pip install --upgrade python-binance
    ```