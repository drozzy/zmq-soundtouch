/*
Copyright 2016 Rene Richard

This file is part of zmq-soundtouch.

zmq-soundtouch is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

zmq-soundtouch is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with zmq-soundtouch.  If not, see <http://www.gnu.org/licenses/>.
*/

package main

import (
	"fmt"
	zmq "github.com/pebbe/zmq4"
	"github.com/redsofa/soundtouch/config"
	"golang.org/x/net/websocket"
	"io"
	"os"
)

//TODO : need to be able to control websocket connection (with other channel?)
func connectWS(msgChan chan string, soundTouchIp, soundTouchPort string) {
	conn, err := websocket.Dial("ws://"+soundTouchIp+
		":"+soundTouchPort, "gabbo", "http://redsofa.ca")
	checkError(err)

	var msg string
	for {
		err := websocket.Message.Receive(conn, &msg)
		if err != nil {
			if err == io.EOF {
				fmt.Println(err)
				close(msgChan)
				break
			}
			fmt.Println("Couldn't receive msg " + err.Error())
			close(msgChan)
			break
		}
		msgChan <- msg
	}
	close(msgChan)
}

func main() {
	msgChan := make(chan string)

	config.ReadConf("./")

	go connectWS(msgChan, config.ClientConf.SoundTouchIP, config.ClientConf.SoundTouchPort)

	clientSecretKey := config.ClientConf.ClientSecretKey
	serverPublicKey := config.ClientConf.ServerPublicKey
	clientPublicKey := config.ClientConf.ClientPublicKey

	//Start authentication engine
	zmq.AuthSetVerbose(true)
	zmq.AuthStart()
	zmq.AuthCurveAdd("*", string(clientPublicKey))

	//  Create and connect client socket
	client, err := zmq.NewSocket(zmq.PUSH)
	checkError(err)

	defer client.Close()

	client.ClientAuthCurve(string(serverPublicKey), string(clientPublicKey), string(clientSecretKey))
	client.Connect("tcp://" + config.ClientConf.PushServerIP + ":" + config.ClientConf.PushServerPort)

	//While we're getting messages on the msgChan channel send them to the push sever
	for msg := range msgChan {
		_, err = client.SendMessage(msg)
		checkError(err)

		fmt.Println("Sent : ", msg)
	}

	zmq.AuthStop()
}

func checkError(err error) {
	if err != nil {
		fmt.Println("Fatal error ", err.Error())
		os.Exit(1)
	}
}
