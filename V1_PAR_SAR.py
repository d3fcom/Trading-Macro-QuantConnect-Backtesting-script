from AlgorithmImports import *

class ParabolicSARTradingAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Configurer les dates du backtest et la devise de base
        self.SetStartDate(2023, 5, 1)  # Début du backtest (1 semaine au hasard)
        self.SetEndDate(2023, 5, 7)    # Fin du backtest
        self.SetCash(100000)           # Capital initial

        # Ajouter la paire USDJPY avec une résolution au tick
        self.usdjpy = self.AddForex("USDJPY", Resolution.Tick).Symbol

        # Initialiser Parabolic SAR avec les paramètres par défaut
        self.psar = ParabolicSAR(0.02, 0.2, 0.02)
        self.RegisterIndicator(self.usdjpy, self.psar, Resolution.Tick)

        # Configurer l'ATR avec une période de 14 à une résolution d'une heure
        self.atr = self.ATR(self.usdjpy, 14, Resolution.Hour)

        # Variable pour suivre les positions
        self.currentPosition = None

        # Stop loss basé sur 5 fois l'ATR
        self.atrMultiplier = 5

    def OnData(self, data):
        # Vérifier si les données Parabolic SAR et ATR sont prêtes
        if not self.psar.IsReady or not self.atr.IsReady:
            return

        price = self.Securities[self.usdjpy].Price
        psar_value = self.psar.Current.Value
        atr_value = self.atr.Current.Value

        # Signaux d'achat et de vente basés sur Parabolic SAR
        if self.currentPosition is None:
            if price > psar_value:
                self.EnterPosition("Long", price, atr_value)
            elif price < psar_value:
                self.EnterPosition("Short", price, atr_value)

    def EnterPosition(self, direction, price, atr_value):
        # Fermer toute position ouverte avant d'ouvrir une nouvelle
        if self.Portfolio[self.usdjpy].Invested:
            self.Liquidate(self.usdjpy)

        # Calculer le stop loss en fonction de l'ATR
        stop_loss_distance = atr_value * self.atrMultiplier

        if direction == "Long":
            # Acheter si le signal Parabolic SAR est en dessous du prix
            quantity = self.Portfolio.Cash / price * 0.01  # 1% du capital
            self.MarketOrder(self.usdjpy, quantity)
            stop_loss_price = price - stop_loss_distance
        else:
            # Vendre si le signal Parabolic SAR est au-dessus du prix
            quantity = -self.Portfolio.Cash / price * 0.01  # 1% du capital
            self.MarketOrder(self.usdjpy, quantity)
            stop_loss_price = price + stop_loss_distance

        # Placer l'ordre de stop loss
        self.StopMarketOrder(self.usdjpy, -quantity, stop_loss_price)

        # Mise à jour de la position actuelle
        self.currentPosition = direction
        self.Debug(f"Entered {direction} position at {price} with stop loss at {stop_loss_price}")

    def OnOrderEvent(self, orderEvent):
        # Gestion des événements d'ordre, fermeture des positions si le stop est atteint
        if orderEvent.Status == OrderStatus.Filled and orderEvent.FillQuantity == 0:
            self.currentPosition = None
