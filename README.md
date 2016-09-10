QwikSwitch-mqtt

QwikSwitch USB modem to mqtt
## Wallplate
```
Number QS1  "QS1"      (Lights) {
        mqtt="
            >[mqtt_pidome:/QwikSwitch/1da123/state:command:*:default]], 
            <[mqtt_pidome:/QwikSwitch/1da123/command:command:REGEX(.*?([0-9]+).*)]
        "
        }

Number QS2  "QS2"      (Lights) {
        mqtt="
            >[mqtt_pidome:/QwikSwitch/1da124/state:command:*:default]], 
            <[mqtt_pidome:/QwikSwitch/1da124/command:command:REGEX(.*?([0-9]+).*)]
        "
        }

rule "qs1"
    when Item QS1 received command
    then
        var new_state = TvLed.state as DecimalType + 20
        if(new_state >100){
            new_state = 100;
        }   
        sendCommand(TvLed, new_state)
end

```

##Dimmer 

Dimmer qsdimmer	"qs button"	   (Lights) {
		mqtt="
			>[mqtt_pidome:/QwikSwitch/1db110/level:command:*:default]], 
			<[mqtt_pidome:/QwikSwitch/1db110/state:state:REGEX(.*?([0-9]+).*)]
		"
		}
		
		

