import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class javabard {

    public static void main(String[] args) {
        String apiKey = "ZQiodFLEELffMX8RDdh8LTHahL2M1vJEVYN74O7RpgkYocajc_6oCX6pL3KM499aN75pyA.";
        String var = "snr0";
        String apiUrl = "https://api.bard.nhs.uk/data/q?text=What%20does%20" + var + "%20mean%20in%20OAI%205G,%20only%20reply%20with%20one%20sentence.";

        // Set the API key as an environment variable (optional)
        System.setProperty("_BARD_API_KEY", apiKey);

        try {
            String content = getBardApiAnswer(apiUrl);
            System.out.println(content);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static String getBardApiAnswer(String apiUrl) throws IOException {
        URL url = new URL(apiUrl);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();

        // Set the request method and headers (e.g., API key)
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Authorization", System.getProperty("_BARD_API_KEY"));

        // Read the response
        BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        StringBuilder response = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            response.append(line);
        }
        reader.close();

        conn.disconnect();

        // Parse the JSON response and extract the answer content
        // You'll need to use a JSON parser like Jackson or Gson here

        return ""; // Return the extracted answer content
    }
}
