class NewsCoreDBRouter:
    """
    A router to control all database operations on models in newscore.
    """

    route_app_labels = ["newscore"]

    def db_for_read(self, model, **hints):
        """
        Attempts to read newscore models from newscore db.
        """
        if model._meta.app_label in self.route_app_labels:
            return "newscore"
        return None

    def db_for_write(self, model, **hints):
        """
        Do not allow write operations on newscore db.
        """
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in newscore app is involved.
        """
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Do not allow migrations on newscore db.
        """
        if app_label in self.route_app_labels:
            return False
        return None
