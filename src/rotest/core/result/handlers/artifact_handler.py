"""Artifact creating handler."""
import os
from zipfile import ZipFile

from rotest.common import config
from .abstract_handler import AbstractResultHandler


class ArtifactHandler(AbstractResultHandler):
    """Artifact creating result handler.

    At the end of the test, this handler creates a zip of the work directory,
    and updates the run data.

    Attributes:
        artifacts_path (str): base dir to create the artifacts in.
        EXTENSTION (str): the extension to append to the artifact file,
            e.g. '.zip'.
        DEFAULT_PROJECT_FOLDER (str): default project dir for the artifact. If
            the user specified a run name, it would be used as project dir.
    """
    NAME = 'artifact'
    EXTENSTION = '.zip'
    DEFAULT_PROJECT_FOLDER = 'default'

    def __init__(self, *args, **kwargs):
        """Initialize the handler and check that the artifacts dir was set."""
        super(ArtifactHandler, self).__init__(*args, **kwargs)
        self.artifacts_path = config.ARTIFACTS_DIR

        if not os.path.isdir(self.artifacts_path):
            os.mkdir(self.artifacts_path)

        run_data = self.main_test.data.run_data
        if run_data is not None and run_data.run_name is not None:
            artifact_folder = os.path.join(self.artifacts_path,
                                           run_data.run_name)

        else:
            artifact_folder = os.path.join(self.artifacts_path,
                                           self.DEFAULT_PROJECT_FOLDER)

        if not os.path.exists(artifact_folder):
            os.mkdir(artifact_folder)

        self.artifact_path = os.path.join(artifact_folder,
                             os.path.basename(self.main_test.work_dir)) \
                             + self.EXTENSTION

        with ZipFile(self.artifact_path, mode='w', allowZip64=True):
            pass

        run_data.artifact_path = self.artifact_path
        if run_data.pk is not None:
            run_data.save()

    def stop_test(self, test):
        """Add the case dir to the artifact.

        Args:
            test (object): test item instance.
        """
        with ZipFile(self.artifact_path, mode='a',
                     allowZip64=True) as artifact:

            for root, _, files in os.walk(test.work_dir):
                for item in files:
                    file_path = os.path.join(root, item)
                    artifact.write(file_path)

    def stop_test_run(self):
        """Add the files of the main work directory to the artifact.

        This is used to copy global files of the run, such as results excel.
        """
        with ZipFile(self.artifact_path, mode='a',
                     allowZip64=True) as artifact:

            for item in os.listdir(self.main_test.work_dir):
                file_path = os.path.join(self.main_test.work_dir, item)
                if os.path.isfile(file_path):
                    artifact.write(file_path)
