import platform
platform.libc_ver = lambda *a, **k: ('', '')

import os
import pandas as pd
import snowflake.connector

QUERY = """
WITH Item_master AS (
    SELECT
        parse_json(THIRDPARTYATTRIBUTES):"id"::string AS Item_Code,
        HASHKEY AS SPIN_ID,
        parse_json(attributes):"SCM_item_type"::string AS Item_Type,
        parse_json(attributes):"temp_sku"::string AS Temp_SKU,
        parse_json(attributes):"super_category/L1"::string AS L1_Category,
        parse_json(attributes):"category/L2"::string AS L2_Category,
        parse_json(attributes):"sub-category/L3"::string AS L3_Category,
        parse_json(attributes):"sub-category/L4"::string AS L4_Category,
        parse_json(attributes):"sub-category/L5"::string AS L5_Category,
        parse_json(attributes):"sub-category/L6"::string AS L6_Category,
        IMAGES,
        parse_json(attributes):"brand_company"::string Brand_Company,
        parse_json(attributes):"brand"::string Brand,
        parse_json(attributes):"product name"::string Item_name,
        BUSINESSLINE
    FROM CMS.CMS_DDB.CMS_SPINS_1
    WHERE BUSINESSLINE = 'INSTAMART'
      AND sortkey = 'SPIN'
)

select
    p.category_final      as CATEGORY_FINAL,
    p.city                as CITY,
    p.city_2              as CITY_2,
    p.tier                as TIER,
    p.store_id            as STORE_ID,
    p.order_date          as ORDER_DATE,
    p.wk                  as WEEK,
    p.orders_total        as ORDERS_TOTAL,
    q.orders_igcc         as ORDERS_IGCC,
    q.orders_igcc / nullif(p.orders_total,0) as QNP
from (
    select Category_Final, city, city_2, tier, store_id, order_date, wk,
    count(distinct parent_id) as orders_total from (
        select
        case when im.l1_category in ( 'Bags Wallets Accessories','Clothing','Electronics and Appliances','Fashion','Home','Jewelry and Hair Accessories','Kitchen and Dining','Makeup','Party Planning','Footwear','Sports and Fitness','Stationery Art Hobbies','Vehicle Care and Accessories','Toys','Books')
        then 'New Comm'
        when im.l1_category in ('Dairy, Bread and Eggs') and im.l2_category not in ('Batters and Chutneys','Indian Breads','Health Drink Mixes','Batter and Breakfast') then 'DBE'
        when im.l2_category in ('Ice Creams') then 'Ice Cream'
        when im.l1_category in ('Fruits and Vegetables') then 'FnV'
        when im.l1_category in ('Meat and Sea Food') then 'Meat'
        else 'Other' end as Category_Final ,im.l1_category
      ,im.l2_category
      ,o.city,o.store_id, o.order_id, o.dt,ci.job_id,im.brand,im.item_name,im.spin_id,o.parent_id
      ,cast(o.dt as date) as order_date
      ,week(cast(o.dt as date)) as wk
      ,to_char(date_trunc('week', cast(o.dt as date)), 'Mon''YY') as Month_Year
      ,case
            when o.city ilike any ('%Bangalore%','%Mysore%','%Mangaluru%','%Salem%') then 'Bangalore'
            when o.city ilike any ('%Chennai%','%Kochi%','%Coimbatore%','%Kozhikode%','%Thiruvananthapuram%','%Pondicherry%','%Trichy%','%Thrissur%') then 'Chennai'
            when o.city ilike any ('%Hyderabad%','%Vizag%','%Vijayawada%','%Guntur%','%Warangal%','%Tirupati%') then 'Hyderabad'
            when o.city ilike any ('%Kolkata%','%Bhubaneswar%','%Ranchi%') then 'Kolkata'
            when o.city ilike any ('%Delhi%','%Gurgaon%','%Noida%','%Noida1%','%Chandigarh%','%Faridabad%','%Lucknow%','%Jaipur%','%Dehradun%','%Amritsar%',
                                    '%Udaipur%','%Ludhiana%','%Kanpur%','%Rajkot%','%Varanasi%') then 'Delhi'
            when o.city ilike any ('%Mumbai%','%Pune%','%Surat%','%Vadodara%','%Nashik%','%Nagpur%','%Ahmedabad%','%Central Goa%','%Indore%','%Bhopal%') then 'Mumbai'
            else 'others'
        end as city_2
      ,case
            when o.city ilike any('%Chennai%','%Noida%','%Noida 1%','%Delhi%','%Bangalore%','%Pune%','%Gurgaon%','%Hyderabad%','%Kolkata%','%Mumbai%') then 'Tier_1'
            else 'Tier_2'
        end as tier
        from analytics.public.im_child_order_fact o
        left join analytics.public.stores_cartitem ci on ci.child_order_id = o.order_id
        inner join
        (select spin_id as spin,sku_id from analytics.public.store_spin_sku_det) cat on ci.itemid=cat.sku_id
        left join Item_master im on im.spin_id = cat.spin
        where o.store_name = 'Instamart'
        and o.dt between '2026-05-01' and current_date()-1
        and o.status in ('DELIVERY_DELIVERED')
        and o.city <> 'Budhwal'
        and Category_Final in ('FnV','DBE','Ice Cream','Meat')
        ) z
    group by all
    )p

    left join(
    select Category_Final, city, city_2, tier, store_id, order_date, week(cast(order_date as date)) as wk,
    count(distinct job_id) orders_IGCC from(
        select distinct b.*,oo.city,oo.store_id,oo.dt,ci.job_id,
        case when im.l1_category in ( 'Bags Wallets Accessories','Clothing','Electronics and Appliances','Fashion','Home','Jewelry and Hair Accessories','Kitchen and Dining','Makeup','Party Planning','Footwear','Sports and Fitness','Stationery Art Hobbies','Vehicle Care and Accessories','Toys', 'Books')
       then 'New Comm'
        when im.l1_category in ('Dairy, Bread and Eggs') and im.l2_category not in ('Batters and Chutneys','Indian Breads','Health Drink Mixes','Batter and Breakfast') then 'DBE'
        when im.l2_category in ('Ice Creams') then 'Ice Cream'
        when im.l1_category in ('Fruits and Vegetables') then 'FnV'
        when im.l1_category in ('Meat and Sea Food') then 'Meat'
        else 'Other' end as Category_Final,im.l1_category
        ,im.l2_category,im.brand,im.item_name,im.spin_id
        ,cast(oo.dt as date) as order_date
        ,case
                when oo.city ilike any ('%Bangalore%','%Mysore%','%Mangaluru%','%Salem%') then 'Bangalore'
                when oo.city ilike any ('%Chennai%','%Kochi%','%Coimbatore%','%Kozhikode%','%Thiruvananthapuram%','%Pondicherry%','%Trichy%','%Thrissur%') then 'Chennai'
                when oo.city ilike any ('%Hyderabad%','%Vizag%','%Vijayawada%','%Guntur%','%Warangal%','%Tirupati%') then 'Hyderabad'
                when oo.city ilike any ('%Kolkata%','%Bhubaneswar%','%Ranchi%') then 'Kolkata'
                when oo.city ilike any ('%Delhi%','%Gurgaon%','%Noida%','%Noida1%','%Chandigarh%','%Faridabad%','%Lucknow%','%Jaipur%','%Dehradun%','%Amritsar%',
                                        '%Udaipur%','%Ludhiana%','%Kanpur%','%Rajkot%','%Varanasi%') then 'Delhi'
                when oo.city ilike any ('%Mumbai%','%Pune%','%Surat%','%Vadodara%','%Nashik%','%Nagpur%','%Ahmedabad%','%Central Goa%','%Indore%','%Bhopal%') then 'Mumbai'
                else 'others'
            end as city_2
        ,case
                when oo.city ilike any('%Chennai%','%Noida%','%Noida 1%','%Delhi%','%Bangalore%','%Pune%','%Gurgaon%','%Hyderabad%','%Kolkata%','%Mumbai%') then 'Tier_1'
                else 'Tier_2'
            end as tier
       from(
            select distinct cast(sif.id as varchar) id,
            trim(bc.value) :: varchar as SKUID
              from analytics.public.stores_igcc_fact_v1 sif,
                lateral flatten (input => sif.TOTALITEMSIMPACTED) bc
                where id in (select distinct order_id from analytics.public.im_child_order_fact
                where status = 'DELIVERY_DELIVERED'
                and dt between '2026-05-01' and current_date()-1
                and store_name = 'Instamart'
                and city <> 'Budhwal'
                )
                and issuedescl1 in ('Bad items delivered','Stores_Quality issue','Stores_Packaging issue','BAD_QUALITY_ITEMS','DAMAGED_ITEMS','EXPIRED_ITEMS','PACKAGING_ISSUES')
                and resolutionsgiven is not null
                and resolutionsgiven in ('REFUND','REPLICATE_ORDER','COUPON')
                and week(resolutiongivendate)=week(order_date)
        )b
        inner join (select distinct order_id,dt,city,store_id from analytics.public.im_child_order_fact
                where status = 'DELIVERY_DELIVERED'
                and dt between '2026-05-01' and current_date()-1
                and store_name = 'Instamart'
                ) oo on oo.order_id=b.id
        left join analytics.public.stores_cartitem ci on ci.child_order_id = b.id
        left join (select spin_id as spin,sku_id from analytics.public.store_spin_sku_det) d on b.skuid=d.sku_id
        left join Item_master im on im.spin_id = d.spin
       )z group by all
       ) q on

p.order_date=q.order_date
and p.category_final=q.category_final
and p.city=q.city
and p.store_id=q.store_id

where p.category_final in ('FnV','DBE','Ice Cream','Meat')
order by p.city, p.store_id, p.order_date asc;
"""

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "igcc_qnp_data.csv")
OUT = os.path.abspath(OUT)

conn = snowflake.connector.connect(
    account=os.environ["SF_ACCOUNT"],
    user=os.environ["SF_USER"],
    role=os.environ.get("SF_ROLE", "FNV_ORG"),
    warehouse=os.environ.get("SF_WH", "DASH_WH"),
    authenticator="externalbrowser",
)
print("Connected.")
cur = conn.cursor()
print("Running query (this may take a few minutes)...")
cur.execute(QUERY, timeout=3600)
rows = cur.fetchall()
cols = [d[0] for d in cur.description]
print(f"Fetched {len(rows)} rows.")
df = pd.DataFrame(rows, columns=cols)
df.to_csv(OUT, index=False)
print(f"Saved to {OUT}")
cur.close(); conn.close()
