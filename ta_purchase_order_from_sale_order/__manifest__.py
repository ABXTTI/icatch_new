# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Purchase Order From Sale Order",
    "author": "AB",
    "version": "14.0.1.2.4",
    "summary": "Create Purchase Orders in Sale Order Form"
    "requirements.",
    "website": "www.ta.net",
    "category": "Purchase Management",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/create_purchase_order.xml",
        "views/select_vendor_wizard.xml",
        "views/inherit_sale_order_for_purchase.xml",
    ],
    "demo": [],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
