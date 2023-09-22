class DBRouter(object):
    default_db = "default"
    info_core_db = "info_core"

    def db_for_read(self, model, **hints):
        if "infocore" in model._meta.model_name:
            return self.info_core_db
        else:
            return self.default_db

    def db_for_write(self, model, **hints):
        if "infocore" in model._meta.model_name:
            return None
        else:
            return self.default_db

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"
