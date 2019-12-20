from typing import Any

import pandas as pd
from absl import app, flags

FLAGS = flags.FLAGS

diskontsatz = 0.025
cf = pd.DataFrame(dict(year=range(2020, 2120), cf=[5] * 100))


def main(_: Any) -> None:
    print(sum(cf['cf'] * 1 / (pow(1 + diskontsatz, cf['year'] - 2020))))
    return


if __name__ == '__main__':
    app.run(main)
