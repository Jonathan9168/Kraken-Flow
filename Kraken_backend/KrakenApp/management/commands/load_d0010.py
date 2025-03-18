import os
import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from ...models import FlowFile, MeterReading


class Command(BaseCommand):
    help = "Load data from a single D0010 (.uff) file or multiple D0010 files in a directory"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Path to a D0010 file or directory")

    def handle(self, *args, **kwargs):
        path = kwargs["path"]

        if os.path.isdir(path):
            file_paths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".uff")]
            if not file_paths:
                self.stdout.write(self.style.WARNING(f"No .uff files found in directory: {path}"))
                return
        elif os.path.isfile(path) and path.endswith(".uff"):
            file_paths = [path]
        else:
            self.stderr.write(self.style.ERROR(f"Invalid file type or path: {path}"))
            raise CommandError(f"File not found: {path}")

        self.process_files(file_paths)

    def process_files(self, file_paths):
        """Processes one or more D0010 (.uff) files"""
        for file_path in file_paths:
            if not os.path.exists(file_path):
                self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
                continue

            self.stdout.write(self.style.SUCCESS(f"Processing file: {file_path}"))

            filename = os.path.basename(file_path)
            if FlowFile.objects.filter(filename=filename).exists():
                self.stdout.write(self.style.WARNING(f"File {filename} already processed. Skipping."))
                continue

            flow_file = FlowFile.objects.create(filename=filename)

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    reader = csv.reader(file, delimiter="|")

                    current_mpan = None
                    current_meter_serial = None
                    readings = []

                    for row in reader:
                        if not row:
                            continue

                        record_type = row[0].strip()

                        if record_type == "026":
                            current_mpan = row[1].strip()

                        elif record_type == "028":
                            current_meter_serial = row[1].strip()

                        elif record_type == "030" and current_mpan and current_meter_serial:
                            try:
                                reading_date = datetime.strptime(row[2].strip(), "%Y%m%d%H%M%S")
                                register_reading = float(row[3].strip())

                                readings.append(
                                    MeterReading(
                                        mpan_core=current_mpan,
                                        meter_serial_number=current_meter_serial,
                                        reading_date=reading_date,
                                        register_reading=register_reading,
                                        flow_file=flow_file,
                                    )
                                )

                            except (IndexError, ValueError) as e:
                                self.stderr.write(
                                    self.style.ERROR(f"Skipping invalid row in {filename}: {row} - {str(e)}"))

                    MeterReading.objects.bulk_create(readings)
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully imported {len(readings)} records from {filename}"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error processing {filename}: {str(e)}"))
