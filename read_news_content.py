import json
import requests
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from threading import Lock


class DatasetProcessor:
    def __init__(self, csv_file, max_workers=5):
        self.csv_file = csv_file
        self.max_workers = max_workers
        self.print_lock = Lock()  # Lock for synchronized printing

    def get_dataset_content(self, url, dataset_id):
        """Retrieve content for a single dataset ID"""
        print(f"\nProcessing dataset: {dataset_id} for URL: {url}")

        api_url = "https://dataset.olostep.com/olostep-p2p-dataset-API"
        headers = {"Authorization": "Bearer olostep_api_test_001201"}
        params = {
            "retrieveMarkdown": "true",  # Changed to get markdown
            "retrieveHtml": "true",
            "datasetId": dataset_id
        }

        try:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()

            # Print the results with thread safety
            with self.print_lock:
                print("\n" + "=" * 50)
                print(f"URL: {url}")
                print(f"Dataset ID: {dataset_id}")
                print("Content:")
                # print(response.body)
                response_dict = json.loads(response.text)
                with open('res.md', 'w') as f:
                    f.write(response_dict['markdown_content'])
                with open('res.html', 'w') as f:
                    f.write(response_dict['html_content'])
                # print(response_dict['markdown_content'])

                # for i in response_dict:
                #     print("key: ", i, "val: ", response_dict[i])
                print("=" * 50 + "\n")

            return True

        except requests.exceptions.RequestException as e:
            print(f"Error processing {dataset_id}: {e}")
            return False

    def process_all_datasets(self):
        """Process all datasets from the CSV file in parallel"""
        print(f"Starting to process datasets from {self.csv_file}")

        # Read the CSV file
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            datasets = [(row['url'], row['content']) for row in reader]

        successful = 0
        failed = 0

        # Process datasets in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_dataset = {
                executor.submit(self.get_dataset_content, url, dataset_id): (url, dataset_id)
                for url, dataset_id in datasets
            }

            for future in as_completed(future_to_dataset):
                url, dataset_id = future_to_dataset[future]
                try:
                    if future.result():
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"Error processing {dataset_id}: {e}")
                    failed += 1

                # Print progress
                total = successful + failed
                print(f"Progress: {total}/{len(datasets)} "
                      f"(Successful: {successful}, Failed: {failed})")

        print("\nProcessing completed!")
        print(f"Total datasets processed: {len(datasets)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")


def main():
    processor = DatasetProcessor('news.csv', max_workers=5)
    processor.process_all_datasets()


if __name__ == "__main__":
    print("Starting dataset content retrieval")
    ds ="defaultDatasetId_6jmtwco2kg"
    processor = DatasetProcessor('news.csv', max_workers=5)

    processor.get_dataset_content("THS URL bloomberg", ds)
    # main()