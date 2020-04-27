from .common import CommonCase, PickingBatchMixin


class BatchPickingCase(CommonCase, PickingBatchMixin):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product B", "type": "product"}
        )
        # which menu we pick should not matter for the batch picking api
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_cluster_picking")
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.picking_type = cls.menu.picking_type_ids
        cls.batch1 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=1)]]
        )
        cls.batch2 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=1)]]
        )
        cls.batch3 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=1)]]
        )
        cls.batch4 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_b, quantity=1)]]
        )
        cls.batch5 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_b, quantity=1)]]
        )
        cls.batch6 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_b, quantity=1)]]
        )
        cls.all_batches = (
            cls.batch1 + cls.batch2 + cls.batch3 + cls.batch4 + cls.batch5 + cls.batch6
        )

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="picking_batch")

    def test_search_empty(self):
        """No batch is available"""
        # Simulate the client asking the list of picking batch
        response = self.service.dispatch("search")
        # none of the pickings are assigned, so we can't work on them
        self.assert_response(response, data={"size": 0, "records": []})

    def test_search(self):
        """Return only draft batches with assigned pickings """
        pickings = self.all_batches.mapped("picking_ids")
        self._fill_stock_for_moves(pickings.mapped("move_lines"))
        pickings.action_assign()
        self.assertTrue(all(p.state == "assigned" for p in pickings))
        # we should not have done batches in list
        self.batch5.state = "done"
        # nor canceled batches
        self.batch6.state = "cancel"
        # we should not have batches in progress
        self.batch4.user_id = self.env.ref("base.user_demo")
        self.batch4.confirm_picking()
        # unless it's assigned to our user
        self.batch3.user_id = self.env.user
        self.batch3.confirm_picking()

        # Simulate the client asking the list of picking batch
        response = self.service.dispatch("search")
        self.assert_response(
            response,
            data={
                "size": 3,
                "records": [
                    {
                        "id": self.batch1.id,
                        "name": self.batch1.name,
                        "picking_count": 1,
                        "move_line_count": 1,
                        "weight": 0.0,
                    },
                    {
                        "id": self.batch2.id,
                        "name": self.batch2.name,
                        "picking_count": 1,
                        "move_line_count": 1,
                        "weight": 0.0,
                    },
                    {
                        "id": self.batch3.id,
                        "name": self.batch3.name,
                        "picking_count": 1,
                        "move_line_count": 1,
                        "weight": 0.0,
                    },
                ],
            },
        )
