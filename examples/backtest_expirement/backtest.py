from datetime import datetime, timedelta

from algorithms import create_algorithm
from app import app
from investing_algorithm_framework import PortfolioConfiguration, \
    pretty_print_backtest_reports_evaluation, BacktestReportsEvaluation, \
    load_backtest_reports


if __name__ == "__main__":
    end_date = datetime(2023, 12, 2)
    start_date = end_date - timedelta(days=100)
    # Add a portfolio configuration of 400 euro initial balance
    app.add_portfolio_configuration(
        PortfolioConfiguration(
            market="BINANCE",
            trading_symbol="EUR",
            initial_balance=400,
        )
    )

    # Run the backtest for each algorithm
    reports = app.run_backtests(
        algorithms=[
            create_algorithm(
                name="9-50-100",
                description="9-50-100",
                fast=9,
                slow=50,
                trend=100
            ),
            create_algorithm(
                name="10-50-100",
                description="10-50-100",
                fast=10,
                slow=50,
                trend=100
            ),
            create_algorithm(
                name="11-50-100",
                description="11-50-100",
                fast=11,
                slow=50,
                trend=100
            ),
            create_algorithm(
                name="9-75-150",
                description="9-75-150",
                fast=9,
                slow=75,
                trend=150
            ),
            create_algorithm(
                name="10-75-150",
                description="10-75-150",
                fast=10,
                slow=75,
                trend=150
            ),
            create_algorithm(
                name="11-75-150",
                description="11-75-150",
                fast=11,
                slow=75,
                trend=150
            ),
            create_algorithm(
                name="20-75-150",
                description="20-75-150",
                fast=20,
                slow=75,
                trend=150
            ),
            create_algorithm(
                name="21-75-150",
                description="21-75-150",
                fast=21,
                slow=75,
                trend=150
            ),
            create_algorithm(
                name="22-75-150",
                description="22-75-150",
                fast=22,
                slow=75,
                trend=150
            ),
            create_algorithm(
                name="23-75-150",
                description="23-75-150",
                fast=23,
                slow=75,
                trend=150
            ),
            create_algorithm(
                name="24-75-150",
                description="24-75-150",
                fast=24,
                slow=75,
                trend=150
            ),
            create_algorithm(
                name="25-75-150",
                description="25-75-150",
                fast=25,
                slow=75,
                trend=150
            ),
            create_algorithm(
                name="20-75-200",
                description="20-75-200",
                fast=20,
                slow=75,
                trend=200
            ),
            create_algorithm(
                name="21-75-200",
                description="24-75-200",
                fast=24,
                slow=75,
                trend=200
            ),
            create_algorithm(
                name="22-75-200",
                description="24-75-200",
                fast=24,
                slow=75,
                trend=200
            ),
            create_algorithm(
                name="23-75-200",
                description="24-75-200",
                fast=24,
                slow=75,
                trend=200
            ),
            create_algorithm(
                name="24-75-200",
                description="24-75-200",
                fast=24,
                slow=75,
                trend=200
            ),
            create_algorithm(
                name="25-75-150",
                description="25-75-200",
                fast=25,
                slow=75,
                trend=200
            ),
        ],
        start_date=start_date,
        end_date=end_date,
        pending_order_check_interval="2h",
    )
    evaluation = BacktestReportsEvaluation(reports)
    pretty_print_backtest_reports_evaluation(evaluation)
    reports = load_backtest_reports(
        "backtest_reports"
    )
    evaluation = BacktestReportsEvaluation(reports)
    pretty_print_backtest_reports_evaluation(evaluation)
