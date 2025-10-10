from django.db import models

class ExchangeRate(models.Model):
    base = models.CharField(max_length=3, default='USD')
    target = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=20, decimal_places=8)
    date = models.DateField(db_index=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('base', 'target', 'date')

    def __str__(self):
        return f"{self.base}->{self.target} ({self.date}): {self.rate}"
