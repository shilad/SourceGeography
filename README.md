SourceGeography
===============

This repo contains Shilad's source code for the Summer 2014 Wikipedia Source Geography project with Heather Ford, Dave Musicant, Brent Hecht, and Mark Graham.

Recreating this project:

## Build the raw url file

1. Create an account on Wikimedia Foundation's Tools Labs.
2. On a labs instance run `get_geo_articles.py` to get the list of geographic articles in every language.
3. On a labs instance run `get_labs_urls.py` to get the list of external urls in every geographic article.
4. Place the external url file in `dat/wmf_source_urls.tsv.bz2`
4. Install WikiBrain for language EN on some computer.
5. Run WmfExtractEnhancer.java on your WikiBrain machine to add more data to the url file.
6. At the end of this step, your final file should be placed in `dat/source_urls.tsv`

## Run  whois queries on all domains

1. Extract all domains by running `AllDomains.java` on your WikiBrain installation.
2. Create an Amazon Web Services (AWS) RDS Postgres installation on a VPC.
3. Fire up an EC2 machine and load the domains into a database by running `create_whois_db.py` with the result of step 1.
4. Run `manage_whois.sh` you will have to change the configuration parameters in the script.

## Scrape web pages for all domains.

1. Extract all cited urls by running `AllUrls.java` on your WikiBrain installation.
2. Fire up an EC2 machine and load the urls into a database by running `create_url_db.py` with the result from the previous step.
4. Run `manage_scraping.sh` you will have to change the configuration parameters in the script.

## Pull down the whois and web scrapes.

1. Backup your amazon RDS instance using `pg_dump`.
2. Restore the postgres database on your computer.
3. Copy the S3 directories with the scrape to your computer (careful! this is about 0.5 TB).
4. Give Dave Musicant the postgres dump and ask him to extract admin countries for the whois results.

# Prepare to infer locations
1. Build set of "interesting" (e.g. non-multimedia) URLs `python build_interesting_urls.py`.
2. Build counts for each url `python build_url_counts.py`.
1. Place Dave's whois results in `dat/whois_results3.tsv`
2. Build url to country file based on whois: `python build_url_to_whois.py`
3. Build url to country file based on wikidata: `python build_wikidata_locations.py`
4. Build prior country distribution: `python build_country_priors.py`

## Infer locations

6. Run the inferrer:
