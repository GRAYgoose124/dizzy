from dizzy import Task


class IngestData(Task):
    """Ingest data from a file"""

    @staticmethod
    def run(ctx):
        with open(ctx["file_path"], "r") as f:
            data = f.read()
        return {"data": data}


class ProcessData(Task):
    """Process data"""

    @staticmethod
    def run(ctx):
        return {"processed_data": ctx["data"].upper()}
