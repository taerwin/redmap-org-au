from django.db import models
from zinnia.models import Entry
from positions import PositionField


class NewsImage(models.Model):
    """Image Model"""

    entry = models.ForeignKey(Entry, related_name="gallery")

    image = models.ImageField('image', upload_to='news/images')
    caption = models.TextField(blank=True)
    position = PositionField(collection="entry")

    class Meta:
        ordering = ["entry", "position"]

    def __unicode__(self):
        return self.caption
