import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

# Market constants
TRADING_MINUTES = 375
SEED = 420  # For reproducibility

# Example daily OHLCV
open_price = 100
high_price = 105
low_price = 95
close_price = 102
total_volume = 1_000_000  # Example: 10 lakh shares


# Helper to generate timestamps
def generate_timestamps(start_time="09:15:00", minutes=375):
    start = pd.Timestamp.today().normalize() + pd.Timedelta(start_time)
    return [start + pd.Timedelta(minutes=i) for i in range(minutes)]


# Helper to adjust the last few minutes of prices
def smart_tail_adjustment(prices, close, high, low, tail_minutes=60):
    """Adjust only the last few minutes towards Close and clip to [Low, High]."""
    adjustment = np.linspace(0, close - prices[-1], tail_minutes)
    prices[-tail_minutes:] += adjustment
    prices = np.clip(prices, low, high)
    return prices


def simulate_linear(open, high, low, close, volume, minutes=375, seed=SEED):
    """
    Simulate intraday stock prices using simple linear interpolation between Open, High, Low, and Close.

    Args:
        open, high, low, close (float): OHLC prices.
        volume (float): Total traded volume.
        minutes (int): Number of minutes (default 375).
        seed (int, optional): Random seed for reproducibility.

    Returns:
        prices (np.ndarray): Simulated prices.
        volumes (np.ndarray): Simulated volumes.
    """
    if seed is not None:
        np.random.seed(seed)

    # Divide the session into three segments: open->high, high->low, low->close
    first_segment = minutes // 3
    second_segment = minutes // 3
    third_segment = minutes - first_segment - second_segment

    prices = np.concatenate(
        [
            np.linspace(open, high, first_segment, endpoint=False),
            np.linspace(high, low, second_segment, endpoint=False),
            np.linspace(low, close, third_segment),
        ]
    )

    # Small noise for realism
    noise = np.random.normal(0, (high - low) / 500, size=minutes)
    prices += noise
    prices = np.clip(prices, low, high)

    # Tail adjustment to ensure it closes at `close`
    prices = smart_tail_adjustment(prices, close, high, low, tail_minutes=15)

    # Distribute volume randomly
    volumes = np.random.dirichlet(np.ones(minutes)) * volume

    return prices, volumes


def simulate_random_walk(open, high, low, close, volume, minutes=375, seed=SEED):
    """
    Simulate intraday prices using a random walk between Open → High/Low → Close.

    Args:
        open, high, low, close (float): OHLC prices.
        volume (float): Total traded volume.
        minutes (int): Number of minutes (default 375).
        seed (int, optional): Random seed for reproducibility.

    Returns:
        prices (np.ndarray): Simulated prices.
        volumes (np.ndarray): Simulated volumes.
    """
    if seed is not None:
        np.random.seed(seed)

    prices = [open]
    for _ in range(minutes - 1):
        step = np.random.normal(0, (high - low) / 100)
        next_price = np.clip(prices[-1] + step, low, high)
        prices.append(next_price)

    prices = np.array(prices)
    # Adjust the tail gently towards 'close'
    prices = smart_tail_adjustment(prices, close, high, low, tail_minutes=15)

    # Force max/min to exactly match High and Low
    i_max = np.argmax(prices[1:-1]) + 1  # +1 because we sliced [1:-1]
    i_min = np.argmin(prices[1:-1]) + 1
    prices[i_max] = high
    prices[i_min] = low

    # Smooth around High/Low
    if 1 < i_max < minutes - 2:
        prices[i_max] = np.mean(prices[i_max - 1 : i_max + 2])
    if 1 < i_min < minutes - 2:
        prices[i_min] = np.mean(prices[i_min - 1 : i_min + 2])

    # Random volume distribution
    volumes = np.random.dirichlet(np.ones(minutes)) * volume

    return prices, volumes


def simulate_geometric_brownian_motion(
    open, high, low, close, volume, minutes=375, mu=0, sigma=0.02, seed=SEED
):
    """
    Simulate intraday stock prices using Geometric Brownian Motion (GBM).

    Args:
        open, high, low, close (float): OHLC prices.
        volume (float): Total traded volume.
        minutes (int): Number of minutes (default 375).
        mu (float): Drift or expected return.
        sigma (float): Volatility (standard deviation of returns).
        seed (int, optional): Random seed for reproducibility.

    Returns:
        prices (np.ndarray): Simulated prices.
        volumes (np.ndarray): Simulated volumes.
    """
    if seed is not None:
        np.random.seed(seed)

    dt = 1 / minutes
    prices = [open]

    for _ in range(minutes - 1):
        random_shock = np.random.normal(0, 1)
        next_price = prices[-1] * np.exp(
            (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * random_shock
        )
        next_price = np.clip(next_price, low, high)
        prices.append(next_price)

    prices = np.array(prices)

    # Tail adjustment to match Close
    prices = smart_tail_adjustment(prices, close, high, low, tail_minutes=15)

    # Force the series to exactly touch High and Low once
    i_max = np.argmax(prices[1:-1]) + 1
    i_min = np.argmin(prices[1:-1]) + 1

    prices[i_max] = high
    prices[i_min] = low

    # Smooth around the High
    if 1 < i_max < minutes - 2:
        prices[i_max - 1] = (prices[i_max - 1] + high) / 2
        prices[i_max + 1] = (prices[i_max + 1] + high) / 2

    # Smooth around the Low
    if 1 < i_min < minutes - 2:
        prices[i_min - 1] = (prices[i_min - 1] + low) / 2
        prices[i_min + 1] = (prices[i_min + 1] + low) / 2

    # Distribute volume randomly
    volumes = np.random.dirichlet(np.ones(minutes)) * volume

    return prices, volumes


def simulate_bezier_noise(open, high, low, close, volume, minutes=375, seed=SEED):
    """
    Simulate intraday stock prices using a smooth Bezier (cubic spline) curve with noise.

    Args:
        open, high, low, close (float): OHLC prices.
        volume (float): Total traded volume.
        minutes (int): Number of minutes (default 375).
        seed (int, optional): Random seed for reproducibility.

    Returns:
        prices (np.ndarray): Simulated prices.
        volumes (np.ndarray): Simulated volumes.
    """
    if seed is not None:
        np.random.seed(seed)

    # Define key points for cubic spline
    x_points = [0, minutes // 3, 2 * minutes // 3, minutes - 1]
    y_points = [open, high, low, close]

    spline = CubicSpline(x_points, y_points)
    prices = spline(np.arange(minutes))

    # Add small random noise
    noise = np.random.normal(0, (high - low) / 300, size=minutes)
    prices += noise
    prices = np.clip(prices, low, high)

    # Tail adjustment to close exactly
    prices = smart_tail_adjustment(prices, close, high, low, tail_minutes=15)

    # Distribute volume randomly
    volumes = np.random.dirichlet(np.ones(minutes)) * volume

    return prices, volumes


if __name__ == "__main__":
    timestamps = generate_timestamps()

    # Simulate prices Linear Interpolation
    print("Simulating prices using Linear Interpolation...")
    prices, volumes = simulate_linear(
        open_price, high_price, low_price, close_price, total_volume
    )
    df = pd.DataFrame({"Timestamp": timestamps, "Close": prices, "Volume": volumes})
    print(df)

    # Simulate prices Random Walk
    print("Simulating prices using Random Walk...")
    prices, volumes = simulate_random_walk(
        open_price, high_price, low_price, close_price, total_volume
    )
    df = pd.DataFrame({"Timestamp": timestamps, "Close": prices, "Volume": volumes})
    print(df)

    # Simulate prices Geometric Brownian Motion
    print("Simulating prices using Geometric Brownian Motion...")
    prices, volumes = simulate_geometric_brownian_motion(
        open_price, high_price, low_price, close_price, total_volume
    )
    df = pd.DataFrame({"Timestamp": timestamps, "Close": prices, "Volume": volumes})
    print(df)

    # Simulate prices Bezier with Noise
    print("Simulating prices using Bezier with Noise...")
    prices, volumes = simulate_bezier_noise(
        open_price, high_price, low_price, close_price, total_volume
    )
    df = pd.DataFrame({"Timestamp": timestamps, "Close": prices, "Volume": volumes})
    print(df)
