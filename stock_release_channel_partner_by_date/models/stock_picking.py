# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models
from odoo.osv import expression


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_release_channel_partner_date_domain(self):
        assert self.scheduled_date
        # FIXME: handle TZ
        return [
            ("partner_id", "=", self.partner_id.id),
            ("date", "=", max(self.scheduled_date.date(), fields.Date.today())),
        ]

    def _get_release_channel_partner_dates(self):
        return self.env["stock.release.channel.partner.date"].search(
            self._get_release_channel_partner_date_domain()
        )

    def _inject_possible_candidate_domain_partners(self):
        """Hooks that could be overridden.

        Return a boolean.
        """
        # Do not inject partners domain if there are channels for this specific
        # delivery address and date
        specific_rcs = self._get_release_channel_partner_dates()
        if specific_rcs:
            return False
        return super()._inject_possible_candidate_domain_partners()

    def _get_release_channel_possible_candidate_domain(self):
        domain = super()._get_release_channel_possible_candidate_domain()
        # Look for a specific release channel at first
        specific_rc_domain = None
        if self.scheduled_date:
            specific_rcs = self._get_release_channel_partner_dates()
            if specific_rcs:
                specific_rc_domain = [("id", "in", specific_rcs.release_channel_id.ids)]
        if specific_rc_domain:
            domain = expression.AND([domain, specific_rc_domain])
        return domain
