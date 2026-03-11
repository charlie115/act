class DBRouter:
    """A router to control all database operations"""

    app_routes = {
        "newscore": {
            "db": "newscore",
            "allow_relation": False,
            "allow_migrate": False,
        },
        "messagecore": {
            "db": "messagecore",
            "allow_relation": False,
            "allow_migrate": True,
        },
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.app_routes:
            return self.app_routes[model._meta.app_label]["db"]
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.app_routes:
            if self.app_routes[model._meta.app_label]["allow_migrate"]:
                return self.app_routes[model._meta.app_label]["db"]
            else:
                return False
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Do not allow relations on messagecore and newscore dbs as they are not in the same db as django.
        Foreign keys on tables outside the same db is not allowed in postgres.
        """

        if obj1._meta.app_label in self.app_routes:
            return self.app_routes[obj1._meta.app_label]["allow_relation"]

        if obj2._meta.app_label in self.app_routes:
            return self.app_routes[obj2._meta.app_label]["allow_relation"]

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.app_routes:
            if (
                db == self.app_routes[app_label]["db"]
                and self.app_routes[db]["allow_migrate"]
            ):
                return True
            else:
                return False
        elif db == "default":
            return None
        else:
            return False
