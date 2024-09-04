class MovingAverageATRTradingAlgorithm(QCAlgorithm):

    def Initialize(self):
        # Initialiser la stratégie
        self.SetStartDate(2023, 1, 1)  # Définir la date de début
        self.SetEndDate(2023, 12, 31)  # Définir la date de fin
        self.SetCash(100000)  # Capital de départ
        self.symbol = self.AddForex("USDJPY", Resolution.Minute).Symbol

        # Timeframe d'analyse
        self.SetTimeZone("America/New_York")
        self.timeframe = 60  # Timeframe de 1 heure

        # Paramètres pour les bandes mobiles
        self.fast_ma_period = 20
        self.slow_ma_period = 50
        self.fast_ma = self.SMA(self.symbol, self.fast_ma_period, Resolution.Hour)
        self.slow_ma = self.SMA(self.symbol, self.slow_ma_period, Resolution.Hour)

        # ATR pour le trailing stop
        self.atr_period = 14
        self.atr = self.ATR(self.symbol, self.atr_period, Resolution.Hour)

        # Assurer que la taille minimale de données est présente avant de trader
        self.SetWarmUp(self.slow_ma_period)

        self.last_trade_direction = None  # Pour éviter les répétitions de trades dans la même direction

    def OnData(self, data):
        # Attendre d'avoir assez de données
        if self.IsWarmingUp:
            return

        # Vérifier si les données de prix sont disponibles
        if not data.ContainsKey(self.symbol):
            return

        price = data[self.symbol].Price

        # Déterminer la direction du trade selon les bandes mobiles
        if self.fast_ma.Current.Value > self.slow_ma.Current.Value and price > self.fast_ma.Current.Value:
            # Signal long
            if self.last_trade_direction != "long":
                self.EnterTrade("long", price)
        elif self.fast_ma.Current.Value < self.slow_ma.Current.Value and price < self.fast_ma.Current.Value:
            # Signal short
            if self.last_trade_direction != "short":
                self.EnterTrade("short", price)

    def EnterTrade(self, direction, price):
        # Fermer les positions existantes avant d'ouvrir une nouvelle
        if self.Portfolio.Invested:
            self.Liquidate(self.symbol)

        # Taille de la transaction (1% du capital disponible)
        quantity = self.CalculateOrderQuantity(self.symbol, 0.01)

        # Entrée en position selon la direction
        if direction == "long":
            self.MarketOrder(self.symbol, quantity)
            self.last_trade_direction = "long"
        elif direction == "short":
            self.MarketOrder(self.symbol, -quantity)
            self.last_trade_direction = "short"

        # Définir le trailing stop à 5 fois l'ATR
        atr_value = self.atr.Current.Value
        stop_price = price - (5 * atr_value) if direction == "long" else price + (5 * atr_value)

        # Stop suiveur
        stop_type = StopMarketOrder(self.symbol, -quantity, stop_price) if direction == "long" else StopMarketOrder(self.symbol, quantity, stop_price)
        self.TrailingStopOrder(self.symbol, quantity, stop_price)

    def OnOrderEvent(self, orderEvent):
        # Suivi des événements d'ordres pour un meilleur contrôle
        if orderEvent.Status == OrderStatus.Filled:
            self.Debug(f"Trade exécuté: {orderEvent.Symbol} à {orderEvent.FillPrice}, quantité: {orderEvent.FillQuantity}")

    def OnEndOfDay(self):
        # Suivi des performances quotidiennes
        self.Debug(f"PNL du jour: {self.Portfolio[self.symbol].UnrealizedProfit}")
