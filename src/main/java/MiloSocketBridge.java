import java.io.*;
import java.net.*;

public class MiloSocketBridge {

    public static final int BRIDGE_PORT = 10000;
    public static final String MILO_IP = "100.64.59.31";
    public static final int MILO_PORT = 4001;

    // 🔥 IMPORTANT: Your correct local interface
    public static final String LOCAL_IP = "100.64.105.57";

    public static void main(String[] args) {

        try {
            // ✅ Reusable server socket
            ServerSocket serverSocket = new ServerSocket();
            serverSocket.setReuseAddress(true);
            serverSocket.bind(new InetSocketAddress(BRIDGE_PORT));

            System.out.println("🚀 Milo Bridge running on port " + BRIDGE_PORT);

            while (true) {

                System.out.println("⏳ Waiting for Python connection...");

                try (
                    Socket pythonClient = serverSocket.accept();
                    BufferedReader inFromPython = new BufferedReader(
                        new InputStreamReader(pythonClient.getInputStream())
                    )
                ) {
                    System.out.println("✅ Python connected");

                    Socket miloSocket = null;
                    OutputStream miloOut = null;

                    try {
                        miloSocket = new Socket();

                        // 🔥 CRITICAL FIX: bind to correct interface
                        miloSocket.bind(new InetSocketAddress(LOCAL_IP, 0));

                        miloSocket.connect(
                            new InetSocketAddress(MILO_IP, MILO_PORT),
                            5000
                        );

                        miloOut = miloSocket.getOutputStream();
                        System.out.println("🤖 Connected to Milo!");

                    } catch (IOException e) {
                        System.out.println("⚠️ Milo not reachable");
                        e.printStackTrace();
                    }

                    String line;

                    while ((line = inFromPython.readLine()) != null) {

                        String speech = line.trim();
                        if (speech.isEmpty()) continue;

                        System.out.println("🗣️ Speech: " + speech);

                        if (miloOut != null) {

                            // ✅ Split sentences to avoid slurring
                            String[] parts = speech.split("[.!?]");

                            for (String part : parts) {
                                part = part.trim();

                                if (!part.isEmpty()) {
                                    String out = "speak " + part + "\n";

                                    miloOut.write(out.getBytes());
                                    miloOut.flush();

                                    System.out.println("➡️ Sent to Milo: " + part);

                                    // ✅ Smooth pacing for Milo speech
                                    try {
                                        Thread.sleep(250);
                                    } catch (InterruptedException ie) {
                                        Thread.currentThread().interrupt();
                                    }
                                }
                            }

                        } else {
                            System.out.println("⚠️ Skipping send (Milo not connected)");
                        }
                    }

                    System.out.println("🔁 Python disconnected");

                    // ✅ Cleanup Milo connection
                    if (miloSocket != null && !miloSocket.isClosed()) {
                        miloSocket.close();
                        System.out.println("🔌 Milo socket closed");
                    }

                } catch (IOException e) {
                    System.err.println("❌ Connection error:");
                    e.printStackTrace();
                }
            }

        } catch (IOException e) {
            System.err.println("❌ Server error:");
            e.printStackTrace();
        }
    }
}
// import java.io.*;
// import java.net.*;

// public class MiloSocketBridge {

//     public static final int BRIDGE_PORT = 10000;  
//     public static final String MILO_IP = "100.64.59.31";
//     public static final int MILO_PORT = 4001;


//     public static void main(String[] args) {

        
//         try {    
//             ServerSocket serverSocket = new ServerSocket();
//             serverSocket.setReuseAddress(true);
//             serverSocket.bind(new InetSocketAddress(BRIDGE_PORT));

//             System.out.println("🚀 Milo Bridge running...");

//                 while (true) {   // 🔥 KEY FIX

//                     try (
//                         Socket pythonClient = serverSocket.accept();
//                         BufferedReader inFromPython = new BufferedReader(
//                             new InputStreamReader(pythonClient.getInputStream())
//                         )
//                     ) {
//                         System.out.println("Python connected");

//                         Socket miloSocket = null;
//                         OutputStream miloOut = null;

//                         try {
//                             miloSocket = new Socket();
//                             // miloSocket.connect(new InetSocketAddress(MILO_IP, MILO_PORT), 2000);
//                             // miloSocket.bind(new InetSocketAddress("100.64.13.63", 0));

//                             miloSocket.connect(new InetSocketAddress(MILO_IP, MILO_PORT), 5000);
//                             miloOut = miloSocket.getOutputStream();
//                             System.out.println("Connected to Milo!");
//                         } catch (IOException e) {
//                             System.out.println("⚠️ Milo not reachable");
//                         }

//                         String line;

//                         while ((line = inFromPython.readLine()) != null) {

//                             String speech = line.trim();
//                             if (speech.isEmpty()) continue;

//                             System.out.println("Speech: " + speech);

//                             if (miloOut != null) {
//                                 // String out = "speak " + speech + "\n";
//                                 // miloOut.write(out.getBytes());
//                                 // miloOut.flush();
//                                 String[] parts = speech.split("[.!?]");
//                                 for (String part : parts) {
//                                     part = part.trim();
//                                     if (!part.isEmpty()) {
//                                         String out = "speak " + part + "\n";
//                                         miloOut.write(out.getBytes());
//                                         miloOut.flush();

//                                         // Thread.sleep(400);  // 🔥 pause between sentences
//                                     }
//                                 }
//                             }
//                         }

//                         System.out.println("🔁 Connection closed. Waiting for next...");

//                     } catch (IOException e) {
//                         System.err.println("Connection error:");
//                         e.printStackTrace();
//                     }
//             } catch (IOException e) {
//                 System.err.println("Server error:");
//                 e.printStackTrace();
//             }

//         }
//     }
// }