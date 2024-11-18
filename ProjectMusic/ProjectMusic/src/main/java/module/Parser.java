package module;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.jspecify.annotations.Nullable;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Wait;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;
import java.util.HashSet;

public class Parser {

    public static void main(String[] args) throws InterruptedException {
        HashSet<String> albumSet = new HashSet<>();
        HashSet<String> artistSet = new HashSet<>();
        HashSet<String> noNameArtistsSet = new HashSet<>();
        String URL = "https://music.yandex.ru/users/music-blog/playlists/2441";
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--disable-gpu");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        options.addArguments("headless");
        options.addArguments("window-size=1920x1080");
        options.addArguments("--lang=ru");
        WebDriver driver = new ChromeDriver(options);
        driver.get(URL);
        Cookie cookie1 = new Cookie("Session_id", "3:1728242305.5.0.1712594388046:8rqeMw:c1.1.2:1|983372656.0.2.3:1712594388|3:10296343.914455.R6hOtRB-7IPXrAHN9u8ku3s5r2U");
        Cookie cookie2 = new Cookie("sessionid2", "3:1728242305.5.0.1712594388046:8rqeMw:c1.1.2:1|983372656.0.2.3:1712594388|3:10296343.914455.fakesign0000000000000000000");
        Cookie cookie3 = new Cookie("yandex_login", "Untrick0");
        Cookie cookie4 = new Cookie("L", "XwlKWQ9haXtvd1VAZ117VUdRXA1hW3FfBSosIQIaLUI=.1712594388.15673.389455.772bef74179a662a722d337a98700881");
        Cookie cookie5 = new Cookie("i", "KjboffRQyEuPzIAT16wM0dQuJH6uMcwVwGf/vJ5pSKqKzlyzzzH9Jj6vvaPKlowlvBqBvjz5zPJbsK+ReSawqcw2cIs=");
        Cookie cookie6 = new Cookie("yandexuid", "3515647581692314328");
        driver.manage().addCookie(cookie1);
        driver.manage().addCookie(cookie2);
        driver.manage().addCookie(cookie3);
        driver.manage().addCookie(cookie4);
        driver.manage().addCookie(cookie5);
        driver.manage().addCookie(cookie6);
        driver.navigate().refresh();
        Wait<WebDriver> wait = new WebDriverWait(driver, Duration.ofSeconds(2));
        WebElement button = wait.until(ExpectedConditions.elementToBeClickable(By.cssSelector("body > div.page-root.page-root_no-player.deco-pane-back.page-root_empty-player > div.centerblock-wrapper.deco-pane.theme_light > div.centerblock > div > div > div.page-playlist__bottom > div.page-playlist__similar-playlists > div.d-more > button")));
        ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView(true);", button);
        button.click();
        albumFinder(driver.getPageSource(), albumSet);
        System.out.println(albumSet);
        for (String albumLink : albumSet) {
            driver.get(albumLink);
            Thread.sleep(250);
            scrollingWebPage(driver);
            artistFinder(driver.getPageSource(), artistSet);
        }
        System.out.println(artistSet);
        System.out.println(artistSet.size());
        for (String noNameArtist : artistSet) {
            driver.get(noNameArtist);
            Thread.sleep(200);
            noNameArtistFinder(driver.getPageSource(),noNameArtist, noNameArtistsSet);
            if (noNameArtistsSet.size() == 15){
                break;
            }
        }
        System.out.println(noNameArtistsSet);
        driver.close();
    }

    public static void albumFinder(String pageSource, HashSet<String> albumSet) {
        Document doc = Jsoup.parse(pageSource);
        Elements playListLinks = doc.select("a[href*=/playlists/]");
        for (Element platListLink : playListLinks) {
            albumSet.add("https://music.yandex.ru" + platListLink.attr("href"));
        }
    }

    public static void artistFinder(String pageSource, HashSet<String> artistSet) {
        Document doc = Jsoup.parse(pageSource);
        Elements playListLinks = doc.select("a[href*=/artist/]");
        for (Element playListLink : playListLinks) {
            artistSet.add("https://music.yandex.ru" + playListLink.attr("href"));
        }
    }

    public static void noNameArtistFinder(String pageSource,String artistPageUrl, HashSet<String> NoNameArtistsSet) {
        Document doc = Jsoup.parse(pageSource);
        String numberOfAuditions = doc.select("body > div.page-root.page-root_no-player.deco-pane-back.page-root_empty-player > div.centerblock-wrapper.deco-pane > div.centerblock > div > div > div.d-generic-page-head > div.d-generic-page-head__main > div.d-generic-page-head__main-top > div.page-artist__summary.typo.deco-typo-secondary > span:nth-child(1)").text();
        numberOfAuditions = numberOfAuditions.replaceAll(" ", "");
        if (!(numberOfAuditions.isEmpty()) && Integer.parseInt(numberOfAuditions) < 100000) {
            NoNameArtistsSet.add(artistPageUrl);
        }
    }

    public static void scrollingWebPage(WebDriver driver) throws InterruptedException {

        JavascriptExecutor js = (JavascriptExecutor) driver;
        int scrollPauseTime = 250;
        int scrollStep = 250;

        long scrollHeight = (long) js.executeScript("return document.body.scrollHeight");

        for (long i = 0; i < scrollHeight; i += scrollStep) {
            js.executeScript("window.scrollBy(0, " + scrollStep + ");");
            Thread.sleep(scrollPauseTime);
        }
    }
}
