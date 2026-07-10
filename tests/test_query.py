from datetime import date, datetime

from rentmanager_api import RQL, QueryParams


def test_rql_filter_formats_scalars_lists_and_dates():
    assert RQL.eq("TenantID", 10) == "TenantID,eq,10"
    assert RQL.in_("TenantID", [4, 5, 6]) == "TenantID,in,(4,5,6)"
    assert RQL.ge("DateCreated", date(2026, 4, 23)) == "DateCreated,ge,2026-04-23"
    assert RQL.lt("UpdateDate", datetime(2026, 4, 23, 18, 15, 30)) == "UpdateDate,lt,2026-04-23T18:15:30"


def test_query_params_emit_wapi_names_and_merge_embed_filter_aliases():
    params = QueryParams(
        fields=["TenantID", "Name"],
        embed=["Contacts"],
        embeds=["Property"],
        filter=RQL.eq("IsActive", True),
        filters=[RQL.ct("Name", "Smith")],
        page_number=2,
        page_size=100,
        no_content=True,
        order_by=["Name DESC", "TenantID"],
        save_options={"IgnoreHardClose": True, "SyncPrimaryContact": False},
    ).to_params()

    assert params == {
        "fields": "TenantID,Name",
        "embed": "Contacts,Property",
        "filters": "IsActive,eq,true;Name,ct,Smith",
        "pagenumber": 2,
        "pagesize": 100,
        "nocontent": "true",
        "orderby": "Name DESC,TenantID",
        "SaveOptions": "IgnoreHardClose,true;SyncPrimaryContact,false",
    }


def test_query_params_preserve_extra_params():
    params = QueryParams(extra={"customFlag": "yes"}).to_params()

    assert params == {"customFlag": "yes"}
