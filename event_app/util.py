from .extensions import db


def reference_col(table: db.Model, nullable: bool = False, pk_name: str = 'id', **kwargs) -> db.Column:
    """Column that adds primary key foreign key reference.
    Usage: ::
        category_id = reference_col('category')
        category = relationship('Category', backref='categories')
    """
    return db.Column(
        db.ForeignKey('{0}.{1}'.format(table.__tablename__, pk_name)),
        nullable=nullable, **kwargs
    )
