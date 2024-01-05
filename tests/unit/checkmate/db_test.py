import sqlalchemy as sa

from checkmate.db import Base


class Child(Base):
    __tablename__ = "child"
    id = sa.Column(sa.Integer, primary_key=True)


class ModelClass(Base):
    __tablename__ = "model_class"
    id = sa.Column(sa.Integer, primary_key=True)
    column = sa.Column(sa.Integer, sa.ForeignKey("child.id"))
    relationship = sa.orm.relationship("Child")


class TestBase:
    def test_repr(self):
        model = ModelClass(id=23, column=46)

        assert repr(model) == "ModelClass(id=23, column=46)"

    def test_repr_is_valid_python(self):
        model = ModelClass(id=23, column=46)

        deserialized_model = eval(repr(model))  # pylint:disable=eval-used

        for attr in (
            "id",
            "column",
        ):
            assert getattr(deserialized_model, attr) == getattr(model, attr)
