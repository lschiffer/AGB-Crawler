# AGB-crawler (Python)

This project's goal is to crawl the privacy policies of applications in online web-stores (currently amazon and google play store), parse them into a structured XML-format and save them with all additional information inside a database. The main languages are german and english privacy policies.

# 1. Step: Crawling
  Each web-store has its own crawler, `crawlPlay.py` for Google Play Store and `crawler_amazon.py` for the Amazon Store. The purpose of these crawlers is only to find and save apps with links to privacy policies and their app-permissions.
  The amazon crawler can be started by the following commands:
  
    import crawler_amazon
    crawler_amazon.crawl(database, maxVisits, maxApps)
  
  where *database* is the name of the SQLite database where all results (ID (App-Name), URL, PERMISSIONS) are stored.
  
# 2. Step: Parsing HTML to XML
  After the crawling process, all HTML files containing the privacy policies need to be crawled and parsed to XML. During this process all unimportant parts and flags of the HTML are removed and the running text of the privacy policy is organized in paragraphs, captions and content as follows:
    
    <dse>
      <para>
        <title>
          Privacy Policy
        </title>
        <text>
        This Privacy Policy ...
        </text>
      </para>
      <para>
        ...
      </para>
    </dse>


## Usage

The parser can be started by executing the file `AGBParser.py`. The name of the input SQLite database containing distinct app IDs, URLs and (optionally) app permissions, each in one column in that order, has to be passed. All other parameters are optional. If multiple input files are passed, they will be processed consecutively. The input files will be associated with the crawler name and the store name at the according position in the options, for example the first crawler name passed will be associated with the first input file given. If the stated output file already exists, it will be updated, else a new file will be created.

### Options

| Option | Feature |
|---|---|
| -h, --help | show help message and exit |
| -i INPUT_FILE, --input=INPUT_FILE | read App-IDs and URLs from sqlite3 database stored in INPUT_FILE (multiple input files possible) |
| -o OUTPUT_FILE, --output=OUTPUT_FILE | write output as sqlite3 database into OUTPUT_FILE (default: output.sqlite) |
| -c CRAWLER, --crawler=CRAWLER | name of the used crawler (multiple names possible) |
| -s STORE, --store=STORE | name of the crawled store (multiple stores possible) |
| -q, --quiet | print no output (only warnings and errors) |
| -d, --debug | print parsed xml |

### Example Usage

Call the parser with its full path (relative to your location). In this example, the location is the top directory `AGB-Crawler` and in that folder are located two input files `GooglePlay.db` and `amazon.db`, that are passed. In the output file `output.db`, each entry created by `GooglePlay.db` has the store name `GooglePlayStore` and the crawler name `CrawlPlay`.

```
code/AGBParser.py -o output.db -i GooglePlay.db -s "GooglePlayStore" -c "CrawlPlay" -i amazon.db -s "AmazonAppstore" -c "CrawlerAmazon"
```

## Required Libraries

We use Python 3.5.1. The following python packages need to be installed:

* beautifulsoup4
* lxml
* urllib3
* langdetect

The parser is dependent on this project's `AGBCheck.py`, which contains automatic quality checks the parser makes use of.

## Approach

As mentioned earlier, the input files are processed consecutively. If the given output file already exists, it is updated, else a new database with all necessary columns is created. For each entry of an input file, the parser carries out the following steps. The app ID, the URL and the permissions are read from the input file.
Then the HTML source of the website is requested, but websites without UTF-8 encoding are skipped. Also only the body is considered and specific tags are removed as explained below. All processing of each website is carried out using the BeautifulSoup format. The remaining HTML source after the mentioned preprocessing is split at the tags `<h3>`, `<h2>`, `<h1>` and `<strong>`. The content of these tags becomes the title of a paragraph, all the text between two such title tags becomes the text of a paragraph in our XML format. Only paragraphs with at least ten characters and privacy policies with at least 100 characters are regarded. The number of empty (or very short) paragraphs is logged in `empty_text_count` as an error value.
On the resulting privacy policy in XML format a number of automatic quality checks defined in `AGBCheck.py` is performed. This includes the inference of the language, the detection of the beginning of the privacy policy, the check for specific keywords and the check for javascript code in the text.
After each processed app, data is written into the output database. This comprises the following columns:

* app_id, text_url, app_permissions (from input database)
* crawler_name, app_storename (optional commandline parameters)
* text_crawldata, text_raw, text_xml (result of parsing)
* empty_text_count (parsing error value)
* language, contains_keywords, contains_js (autocheck)

### Removal of Specific Tags

Before the actual parsing, a variety of tags which most likely contain no relevant content is stripped from the raw HTML source. First some tags with undesired names are removed, for example *script*, *header*, *img* and *meta*. Then tags with specific content are removed, namely *back to top* and *view full policy*. Also tags with certain keywords in their id or class are pruned off, such as *news*, *subscribe*, *rss*, *download*, *toc* and many more. Tags containing the keywords *menu* or *sidebar* are only removed, if their length falls below a threshold.

# 3. Step: Cleanup 
  The final step in the workflow is to remove all duplicate privacy policies, determine the language of the text and evaluate if it really is a privacy policy by checking for keywords and manual inspection.
  The manual inspection is done by assigning a score-value between 0 and 100 to each sucessfully parsed privacy policy with the following meaning:
  
  value | meaning
  --- | ---
  0     | document is NO privacy policy
  20    | document partly contains privacy policy related information but also non-relevant information (page header, footer, subscription information etc.)
  40    | document contains noticeable parsing errors or part of the information is missing
  60    | document is kind of a privacy policy but with 'strange' content (no legitimate content)
  80    | document is a privacy policy but has a few errors (e.g. empty title)
  100   | document is a privacy policy with good quality
  
  
  To analyse the final database regarding language distribution depending on the quality, the following lines of R-code can be used:
  
  ```R
  library(RSQLite)
  library(ggplot2)
  # open sqlite database connection
  con <- dbConnect(SQLite(), "20-01-16.db")
  # to list tables in database
  dbListTables(con)
  # get table 'agb' as data frame
  agb <- dbGetQuery(con, "select * from AGB")

  ### a few useful function to get some general information
  # number of privacy policies with successful parsing
  length(which(agb$text_xml != ""))
  # number of duplicates
  length(which(agb$text_xml != "" & agb$duplicate == 1))
  # number of duplicates in Google store
  length(which(agb$text_xml != "" & agb$duplicate == 1 & agb$app_storename == "GooglePlayStore"))
  # table with languages and their frequencies
  count(agb$language)

  # set duplicate values to 1 or 0 (NA means no duplicate)
  agb$duplicate <- ifelse(is.na(agb$duplicate) | agb$duplicate == 0, 0, 1)
  # set factor levels of language in decreasing order of their frequencies
  agb$language <- factor(agb$language, levels = names(table(agb$language))[order(table(agb$language), decreasing = T)])

  # plot with score in manual checks depending on language
  p <- ggplot(subset(agb, agb$text_xml != "" & agb$duplicate == 0), aes(x = check_man, group = language, fill = language)) + geom_bar(width = 10) + scale_x_discrete("", breaks = c(0, 20, 40, 60, 80, 100), labels = c("Keine DSB", "Ausschuss", "Parsing Fehler", "Inhaltsfehler", "Leerer Titel", "DSB (gute Qualität)"), expand = c(.05,0)) + scale_y_continuous("", breaks = pretty_breaks(n=5)) + scale_fill_brewer("Sprache", palette = "Dark2") + theme_bw() + theme(text = element_text(size=12))
  # violin plots with counted errors during parsing process depending on score in manual checks and language
  q <- ggplot(subset(agb, agb$text_xml != "" & agb$duplicate == 0), aes(x = check_man, y = empty_text_count, group = interaction(language, check_man), colour = language, fill = language)) + geom_violin(adjust = .5, width = 20) + scale_x_discrete("", breaks = c(0, 20, 40, 60, 80, 100), labels = c("Keine DSB", "Ausschuss", "Parsing Fehler", "Inhaltsfehler", "Leerer Titel", "DSB (gute Qualität)"), expand = c(.05,0)) + scale_y_continuous("Parsing Error Count (empty_text)", breaks = pretty_breaks(n=5)) + scale_colour_brewer("Sprache", palette = "Dark2") + scale_fill_brewer("Sprache", palette = "Dark2") + theme_bw() + theme(text = element_text(size=12))
  # boxplots with number of characters in xml depending on score in manual checks and language
  r <- ggplot(subset(agb, agb$text_xml != "" & agb$duplicate == 0), aes(x = check_man, y = nchar(text_xml), group = interaction(language, check_man), fill = language)) + geom_boxplot(width = 10) + scale_x_discrete("", breaks = c(0, 20, 40, 60, 80, 100), labels = c("Keine DSB", "Ausschuss", "Parsing Fehler", "Inhaltsfehler", "Leerer Titel", "DSB (gute Qualität)"), expand = c(.05,0)) + scale_y_log10("Anzahl Zeichen in XML", breaks = c(1, 10, 100, 1000, 10000, 100000)) + scale_colour_brewer("Sprache", palette = "Dark2") + scale_fill_brewer("Sprache", palette = "Dark2") + theme_bw() + theme(text = element_text(size=12))
  
  # save plots as pdf
  ggsave("out.pdf", p, device = cairo_pdf, h = 6, w = 8)
  ```
