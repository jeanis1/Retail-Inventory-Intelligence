"""Step 1: list every mock.shop product handle into input/mock.shop.csv."""

import csv

from engine import INPUT_PATH, iter_product_handles, load_workflow


def main():
    handles = list(iter_product_handles(load_workflow()))

    INPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["handle"])
        writer.writerows([handle] for handle in handles)

    print(f"Wrote {len(handles)} product handles to {INPUT_PATH}")


if __name__ == "__main__":
    main()
