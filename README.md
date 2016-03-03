# AGB-crawler (Python)

This project's goal is to crawl the privacy policies of applications in online web-stores (currently amazon and google play store), parse them into a structured XML-format and save them with all additional information inside a database. The main languages are german and english privacy policies.

# 1. Step: Crawling
  Each web-store has its own crawler; *crawlPlay.py* for Google Play Store and *crawler_amazon.py* for the Amazon Store. The purpose of these crawlers is only to find and save apps with links to privacy policies and their app-permissions.
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
    
# 3. Step: Cleanup 
  The final step in the workflow is to remove all duplicate privacy policies, determine the language of the text and evaluate if it really is a privacy policy by checking for keywords and manual inspection.
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
