let latestMarketData = null;


// ======================================================
// AUTO TRADE POPUP
// ======================================================

function showAutoTradePopup(trade) {

    // Already existing popup இருந்தா remove
    const oldPopup = document.getElementById("autoTradePopup");

    if (oldPopup) {
        oldPopup.remove();
    }


    const popup = document.createElement("div");

    popup.id = "autoTradePopup";

    popup.innerHTML = `
        <div class="auto-popup-box">

            <div class="auto-popup-icon">
                ✓
            </div>

            <h2>
                Auto Trade Executed
            </h2>

            <p class="auto-popup-status">
                Paper BUY + Paper SELL completed
            </p>

            <div class="auto-popup-details">

                <div>
                    <span>Buy From</span>
                    <strong>${trade.buy}</strong>
                </div>

                <div>
                    <span>Sell On</span>
                    <strong>${trade.sell}</strong>
                </div>

                <div>
                    <span>Buy Price</span>
                    <strong>${formatPrice(trade.buy_price)} USDT</strong>
                </div>

                <div>
                    <span>Sell Price</span>
                    <strong>${formatPrice(trade.sell_price)} USDT</strong>
                </div>

                <div>
                    <span>Fees</span>
                    <strong>${formatPrice(trade.fees)} USDT</strong>
                </div>

                <div>
                    <span>Profit</span>
                    <strong class="popup-profit">
                        +${formatPrice(trade.profit)} USDT
                    </strong>
                </div>

            </div>

            <button
                class="auto-popup-close"
                onclick="closeAutoTradePopup()"
            >
                Close
            </button>

        </div>
    `;


    document.body.appendChild(popup);


    // Small delay for animation
    setTimeout(() => {

        popup.classList.add("show");

    }, 50);


    // Automatically close after 6 seconds
    setTimeout(() => {

        closeAutoTradePopup();

    }, 6000);
}


// ======================================================
// CLOSE POPUP
// ======================================================

function closeAutoTradePopup() {

    const popup =
        document.getElementById("autoTradePopup");


    if (!popup) {
        return;
    }


    popup.classList.remove("show");


    setTimeout(() => {

        popup.remove();

    }, 300);
}


// ======================================================
// LOAD MARKET DATA
// ======================================================

async function loadMarketData() {

    try {

        const response =
            await fetch("/api/market");


        const result =
            await response.json();


        if (!result.success) {

            document.getElementById("status").innerText =
                "❌ Unable to fetch market data";

            return;
        }


        const data =
            result.data;


        latestMarketData =
            data;


        // ==================================================
        // EXCHANGE PRICES
        // ==================================================

        if (
            data.prices.Binance !== undefined &&
            document.getElementById("binancePrice")
        ) {

            document.getElementById("binancePrice").innerText =
                formatPrice(data.prices.Binance);
        }


        if (
            data.prices.Bybit !== undefined &&
            document.getElementById("bybitPrice")
        ) {

            document.getElementById("bybitPrice").innerText =
                formatPrice(data.prices.Bybit);
        }


        if (
            (data.prices.Coinbase !== undefined || data.prices.Kraken !== undefined) &&
            document.getElementById("coinbasePrice")
        ) {

            document.getElementById("coinbasePrice").innerText =
                formatPrice(data.prices.Coinbase || data.prices.Kraken);
        }


        // ==================================================
        // BEST BUY
        // ==================================================

        if (document.getElementById("buyExchange")) {

            document.getElementById("buyExchange").innerText =
                data.buy_exchange;
        }


        if (document.getElementById("buyPrice")) {

            document.getElementById("buyPrice").innerText =
                formatPrice(data.buy_price) + " USDT";
        }


        // ==================================================
        // BEST SELL
        // ==================================================

        if (document.getElementById("sellExchange")) {

            document.getElementById("sellExchange").innerText =
                data.sell_exchange;
        }


        if (document.getElementById("sellPrice")) {

            document.getElementById("sellPrice").innerText =
                formatPrice(data.sell_price) + " USDT";
        }


        // ==================================================
        // DIFFERENCE
        // ==================================================

        if (document.getElementById("difference")) {

            document.getElementById("difference").innerText =
                formatPrice(data.difference);
        }


        // ==================================================
        // FEES
        // ==================================================

        if (document.getElementById("fees")) {

            document.getElementById("fees").innerText =
                formatPrice(data.fees);
        }


        // ==================================================
        // NET PROFIT
        // ==================================================

        const profitElement =
            document.getElementById("netProfit");


        if (profitElement) {

            profitElement.innerText =
                formatPrice(data.net_profit);


            if (data.net_profit > 0) {

                profitElement.classList.add(
                    "profit-positive"
                );

                profitElement.classList.remove(
                    "profit-negative"
                );

            } else {

                profitElement.classList.add(
                    "profit-negative"
                );

                profitElement.classList.remove(
                    "profit-positive"
                );
            }
        }


        // ==================================================
        // STATUS
        // ==================================================

        const status =
            document.getElementById("status");


        if (status) {

            if (data.net_profit > 0) {

                status.innerText =
                    "🟢 Profitable — Automatic Paper Trading";

            } else {

                status.innerText =
                    "🔴 No Profitable Arbitrage Opportunity";
            }
        }


        // ==================================================
        // LAST UPDATED
        // ==================================================

        const lastUpdated =
            document.getElementById("lastUpdated");


        if (lastUpdated) {

            lastUpdated.innerText =
                "Last Updated: " +
                new Date().toLocaleTimeString();
        }


        // ==================================================
        // AUTO TRADE RESULT
        // ==================================================

        if (result.auto_trade) {

            const autoTrade =
                result.auto_trade;


            if (autoTrade.success) {

                // ------------------------------------------
                // SHOW POPUP
                // ------------------------------------------

                showAutoTradePopup(
                    autoTrade.trade
                );


                // ------------------------------------------
                // UPDATE TRADE MESSAGE
                // ------------------------------------------

                const message =
                    document.getElementById(
                        "tradeMessage"
                    );


                if (message) {

                    message.innerText =
                        "🟢 PAPER BUY + PAPER SELL EXECUTED";
                }


                // ------------------------------------------
                // REFRESH TRADE HISTORY
                // ------------------------------------------

                await loadTradeHistory();
            }
        }


    } catch (error) {

        console.error(
            "Market Data Error:",
            error
        );


        const status =
            document.getElementById("status");


        if (status) {

            status.innerText =
                "❌ Connection Error";
        }
    }
}


// ======================================================
// LOAD TRADE HISTORY
// ======================================================

async function loadTradeHistory() {

    try {
        const response = await fetch("/api/trades");
        const result = await response.json();

        const table = document.getElementById("tradeTable") || document.getElementById("tradeHistory");

        if (!table) {
            return;
        }

        table.innerHTML = "";

        if (!result.success || !result.trades || result.trades.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="10" style="text-align:center; padding:30px; color:#64748b;">
                        No trades executed yet
                    </td>
                </tr>
            `;
            return;
        }

        result.trades.forEach(trade => {
            const row = document.createElement("tr");
            const buyEx = trade.buy_exchange || trade.buy || "--";
            const sellEx = trade.sell_exchange || trade.sell || "--";
            const profit = Number(trade.profit || 0);

            row.innerHTML = `
                <td>
                    <span style="font-family:monospace; font-size:11px; background:#0c1526; padding:3px 6px; border-radius:4px; color:#3b82f6;">${trade.buy_order_id || 'AUTO-BUY'}</span>
                </td>
                <td>
                    <strong style="color:#22c55e;">${buyEx}</strong>
                    <span style="color:#64748b; margin:0 4px;">➔</span>
                    <strong style="color:#ef4444;">${sellEx}</strong>
                </td>
                <td>$${formatPrice(trade.buy_price)}</td>
                <td>$${formatPrice(trade.sell_price)}</td>
                <td>${Number(trade.btc_amount || 0).toFixed(4)} BTC</td>
                <td>$${Number(trade.trade_amount || 0).toFixed(0)}</td>
                <td>${Number(trade.slippage || 0).toFixed(2)}%</td>
                <td>$${formatPrice(trade.fees)}</td>
                <td class="${profit >= 0 ? "profit-positive" : "profit-negative"}">
                    ${profit >= 0 ? "+" : ""}$${formatPrice(profit)} USDT
                </td>
                <td>${formatDateTime(trade.created_at)}</td>
            `;

            table.appendChild(row);
        });

    } catch (error) {
        console.error("Trade History Error:", error);
    }
}


// ======================================================
// FORMAT PRICE
// ======================================================

function formatPrice(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "--";
    }


    return Number(value).toFixed(2);
}


// ======================================================
// FORMAT DATE TIME
// ======================================================

function formatDateTime(value) {

    if (!value) {

        return "--";
    }


    const date =
        new Date(
            value.replace(" ", "T") + "Z"
        );


    return date.toLocaleString();
}


// ======================================================
// INITIAL LOAD
// ======================================================

loadMarketData();

loadTradeHistory();


// ======================================================
// AUTO REFRESH
// ======================================================

setInterval(
    loadMarketData,
    5000
);

// ======================================================
// AUTO TRADE POPUP
// ======================================================

function showAutoTradePopup(trade) {

    console.log("🔔 showAutoTradePopup called", trade);

    const popup = document.getElementById("autoTradePopup");

    if (!popup) {
        console.error("❌ autoTradePopup element not found");
        return;
    }

    const buyExchange =
        trade.buy || trade.buy_exchange || "--";

    const sellExchange =
        trade.sell || trade.sell_exchange || "--";

    const buyPrice =
        trade.buy_price !== undefined
            ? Number(trade.buy_price).toFixed(2)
            : "--";

    const sellPrice =
        trade.sell_price !== undefined
            ? Number(trade.sell_price).toFixed(2)
            : "--";

    const fees =
        trade.fees !== undefined
            ? Number(trade.fees).toFixed(2)
            : "--";

    const profit =
        trade.profit !== undefined
            ? Number(trade.profit).toFixed(2)
            : "--";


    popup.innerHTML = `

        <div class="auto-trade-popup">

            <button
                class="popup-close"
                onclick="closeAutoTradePopup()">
                ×
            </button>

            <div class="popup-icon">
                🤖
            </div>

            <h2>
                Automatic Trade Executed
            </h2>

            <p class="popup-success">
                🟢 Paper Buy + Paper Sell completed
            </p>

            <div class="popup-trade-info">

                <div class="popup-row">
                    <span>Buy From</span>
                    <strong>
                        ${buyExchange}
                    </strong>
                </div>

                <div class="popup-row">
                    <span>Buy Price</span>
                    <strong>
                        ${buyPrice} USDT
                    </strong>
                </div>

                <div class="popup-row">
                    <span>Sell On</span>
                    <strong>
                        ${sellExchange}
                    </strong>
                </div>

                <div class="popup-row">
                    <span>Sell Price</span>
                    <strong>
                        ${sellPrice} USDT
                    </strong>
                </div>

                <div class="popup-row">
                    <span>Fees</span>
                    <strong>
                        ${fees} USDT
                    </strong>
                </div>

                <div class="popup-row popup-profit">
                    <span>Net Profit</span>
                    <strong>
                        +${profit} USDT
                    </strong>
                </div>

            </div>

            <div class="popup-footer">
                Automatic paper trading is active
            </div>

        </div>
    `;


    popup.classList.add("popup-show");


    // Automatically close after 6 seconds

    setTimeout(() => {

        closeAutoTradePopup();

    }, 6000);
}


// ======================================================
// CLOSE POPUP
// ======================================================

function closeAutoTradePopup() {

    const popup =
        document.getElementById("autoTradePopup");

    if (!popup) {
        return;
    }

    popup.classList.remove("popup-show");
}