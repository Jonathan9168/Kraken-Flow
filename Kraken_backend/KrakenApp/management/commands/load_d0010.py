import os
import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from ...models import FlowFile, MeterReading


class Command(BaseCommand):
    help = "Load data from a single D0010 (.uff) file or multiple D0010 files in a directory"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Path to a D0010 file or directory")

    def handle(self, *args, **kwargs):
        path = kwargs["path"]
        file_paths = self.get_file_paths(path)
        if not file_paths:
            return
        self.process_files(file_paths)

    def get_file_paths(self, path):
        """Handles file and directory checks in one place."""
        if os.path.isdir(path):
            file_paths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".uff")]
            if not file_paths:
                self.stdout.write(self.style.WARNING(f"No .uff files found in directory: {path}"))
                return []
        elif os.path.isfile(path) and path.endswith(".uff"):
            file_paths = [path]
        else:
            self.stderr.write(self.style.ERROR(f"Invalid file type or path: {path}"))
            raise CommandError(f"File not found: {path}")
        return file_paths

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

            try:
                with transaction.atomic():
                    flow_file = FlowFile.objects.create(filename=filename)
                    readings = list(self.parse_uff_file(file_path, flow_file))
                    if readings:
                        MeterReading.objects.bulk_create(readings)
                        self.stdout.write(
                            self.style.SUCCESS(f"Successfully imported {len(readings)} records from {filename}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error processing {filename}: {str(e)}"))

    def parse_uff_file(self, file_path, flow_file):
        """Generator function to parse a .uff file and yield MeterReading objects."""
        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter="|")

            current_mpan = None
            current_meter_serial = None

            for row in reader:
                if not row:
                    continue

                record_type = row[0].strip()

                if record_type == "026":
                    current_mpan = self.handle_026(row)
                    current_meter_serial = None  # Reset meter serial to prevent mismatches

                elif record_type == "028":
                    current_meter_serial = self.handle_028(row)

                elif record_type == "030" and current_mpan and current_meter_serial:
                    reading = self.handle_030(row, current_mpan, current_meter_serial, flow_file, file_path)
                    if reading:
                        yield reading

    def handle_026(self, row):
        """Handles 026 record type, returning the MPAN."""
        return row[1].strip()

    def handle_028(self, row):
        """Handles 028 record type, returning the Meter Serial Number."""
        return row[1].strip()

    def handle_030(self, row, current_mpan, current_meter_serial, flow_file, file_path):
        """Handles 030 record type, returning a MeterReading object."""
        try:
            reading_date = datetime.strptime(row[2].strip(), "%Y%m%d%H%M%S")
            register_reading = float(row[3].strip())

            return MeterReading(
                mpan_core=current_mpan,
                meter_serial_number=current_meter_serial,
                reading_date=reading_date,
                register_reading=register_reading,
                flow_file=flow_file,
            )
        except (IndexError, ValueError) as e:
            self.stderr.write(self.style.ERROR(f"Skipping invalid row in {file_path}: {row} - {str(e)}"))
            return None
