from dizzy import Task


class IngestData(Task):
    """Ingest data from a file"""

    @staticmethod
    def run(ctx):
        return {"data": "Hello, world!"}
        # needt o make some sort of action to grab data from somewhere
        # or options to pass in data
        with open(ctx["file_path"], "r") as f:
            data = f.read()
        return {"data": data}


class ProcessData(Task):
    """Process data"""

    @staticmethod
    def run(ctx):
        return {"processed_data": ctx["data"].upper()}


class AnalyzeResults(Task):
    """Analyze processed data"""

    @staticmethod
    def run(ctx):
        return {"analysis": "Data is all uppercase."}
