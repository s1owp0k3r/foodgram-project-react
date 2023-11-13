import csv
import os

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Import data from a CSV file into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csvfile", type=str, help="Specify the CSV file path."
        )

    def handle(self, *args, **options):
        path = options["csvfile"]
        model = Ingredient

        if not os.path.exists(path):
            raise CommandError(
                self.stdout.write(
                    self.style.ERROR(f"File {path} does not exist.")
                )
            )

        rows = 0
        successful = 0
        self.stdout.write("Importing data for Ingredient model...")

        with open(path, encoding="utf-8", mode="r") as file:
            csv_read = csv.reader(file, delimiter=',')
            for row in csv_read:
                rows += 1
                try:
                    model.objects.get_or_create(name=row[0], measurement_unit=row[1])
                    successful += 1
                except Exception as error:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error in row {rows}.\n'
                            f"Error: - {error}"
                        )
                    )
        self.stdout.write(
            self.style.SUCCESS(
                f"Finished importing data for Ingredient model.\n"
                f"Total rows: {rows}. "
                f"Successful: {successful}. "
                f"Failed: {abs(rows - successful)}."
            )
        )
